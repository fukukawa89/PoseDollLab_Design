/* Rev O3 G0 + six remote nodes. PD41 v1 remains unchanged; no calibration, UDP, IMU or OTP writes.
 * ESP-IDF 6.1 esp_twai API. One pending TX buffer; it stays alive until completion.
 * Each acquired cohort starts blank. A missing node cannot reuse older angles.
 */
#include <stdatomic.h>
#include <string.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "driver/usb_serial_jtag.h"
#include "esp_twai.h"
#include "esp_twai_onchip.h"
#include "esp_timer.h"
#include "esp_rom_sys.h"
#include "esp_random.h"
#include "esp_mac.h"
#include "esp_err.h"
#include "pd41_core.h"
#include "pd41_gateway.h"
#include "pd41_session.h"
enum { NODE=CONFIG_PD_NODE_ID, IO_FAIL=1, PARITY_FAIL=2, SENSOR_ERROR=4, MAGNET_FAIL=8, NONZERO_OTP=16 };
enum { CAN_EPOCH=0x080, CAN_SYNC=0x081, CAN_BOOT=0x100, CAN_ACK=0x120, CAN_END=0x180, CAN_PAIR=0x200 };
typedef struct {uint64_t us;uint32_t id;uint8_t bytes[8];} rx_event_t;
#if !CONFIG_PD_EXTERNAL_GATEWAY
static spi_device_handle_t sensor;
#endif
static twai_node_handle_t can;
static QueueHandle_t receive_queue;
static SemaphoreHandle_t transmit_done;
static atomic_bool rx_overflow;
static volatile bool tx_success;
static twai_frame_t transmit_frame;
static uint8_t transmit_bytes[8];
static uint64_t boot_id;
static uint64_t clock_us(void){return (uint64_t)esp_timer_get_time();}
static uint64_t random_id(void){uint64_t n=0;while(!n)n=((uint64_t)esp_random()<<32)|esp_random();return n;}
#if CONFIG_PD_EXTERNAL_GATEWAY
static void sleep_until(uint64_t deadline){while(clock_us()<deadline)vTaskDelay(1);}
#endif
#if !CONFIG_PD_EXTERNAL_GATEWAY
static uint16_t even_parity(uint16_t v){unsigned p=0;for(unsigned i=0;i<15;i++)p^=(v>>i)&1;return v|((uint16_t)p<<15);}
static bool even(uint16_t v){unsigned p=0;for(unsigned i=0;i<16;i++)p^=(v>>i)&1;return p==0;}
static esp_err_t spi_word(unsigned port,uint16_t tx,uint16_t *rx){
    uint8_t a[2]={(uint8_t)(tx>>8),(uint8_t)tx},b[2]={0};
    spi_transaction_t t={.length=16,.tx_buffer=a,.rx_buffer=b};
    gpio_set_level(pd_cs_gpio[port],0);esp_rom_delay_us(1);
    esp_err_t e=spi_device_polling_transmit(sensor,&t);
    esp_rom_delay_us(1);gpio_set_level(pd_cs_gpio[port],1);esp_rom_delay_us(1);
    *rx=((uint16_t)b[0]<<8)|b[1];return e;
}
static uint16_t read_reg(unsigned port,uint16_t addr,uint16_t *value){
    uint16_t dummy=0,r=0,flags=0;
    esp_err_t a=spi_word(port,even_parity(0x4000|addr),&dummy),b=spi_word(port,0,&r);
    if(a!=ESP_OK || b!=ESP_OK)flags|=IO_FAIL;
    if(!even(r))flags|=PARITY_FAIL;
    if(r&0x4000)flags|=SENSOR_ERROR;
    *value=r&0x3fff;return flags;
}
static uint16_t read_axis(unsigned port){
    uint16_t diag=0,mag=0,angle=0,hi=0,lo=0,dummy=0,flags=0;
    flags|=read_reg(port,0x3ffd,&diag);flags|=read_reg(port,0x3ffe,&mag);flags|=read_reg(port,0x3fff,&angle);
    flags|=read_reg(port,0x0016,&hi);flags|=read_reg(port,0x0017,&lo);
    if(!(diag&0x100) || (diag&0xe00))flags|=MAGNET_FAIL;
    if(((hi&255)<<6)|(lo&63))flags|=NONZERO_OTP;
    if(flags&SENSOR_ERROR)(void)read_reg(port,1,&dummy); /* read-to-clear only */
    return flags?(uint16_t)(PD_FAULT|flags):angle;
}
static void spi_setup(void){
    uint64_t mask=0;for(unsigned i=0;i<9;i++)mask|=1ULL<<pd_cs_gpio[i];
    gpio_config_t pins={.pin_bit_mask=mask,.mode=GPIO_MODE_OUTPUT};ESP_ERROR_CHECK(gpio_config(&pins));
    for(unsigned i=0;i<9;i++)gpio_set_level(pd_cs_gpio[i],1);
    spi_bus_config_t bus={.mosi_io_num=11,.miso_io_num=13,.sclk_io_num=12,.quadwp_io_num=-1,.quadhd_io_num=-1,.max_transfer_sz=2};
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST,&bus,SPI_DMA_DISABLED));
    spi_device_interface_config_t device={.clock_speed_hz=250000,.mode=1,.spics_io_num=-1,.queue_size=1};
    ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST,&device,&sensor));
    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_NUM_13,GPIO_PULLUP_ONLY));
}
#endif
static bool on_rx(twai_node_handle_t handle,const twai_rx_done_event_data_t *edata,void *context){
    (void)edata;(void)context;rx_event_t e={.us=clock_us()};twai_frame_t f={.buffer=e.bytes,.buffer_len=8};BaseType_t woken=pdFALSE;
    if(twai_node_receive_from_isr(handle,&f)==ESP_OK && !f.header.ide && !f.header.rtr && !f.header.fdf && f.header.dlc==8){
        e.id=f.header.id;if(xQueueSendFromISR(receive_queue,&e,&woken)!=pdTRUE)atomic_store(&rx_overflow,true);
    }
    return woken==pdTRUE;
}
static bool on_tx(twai_node_handle_t handle,const twai_tx_done_event_data_t *edata,void *context){
    (void)handle;(void)context;BaseType_t woken=pdFALSE;tx_success=edata->is_tx_success;xSemaphoreGiveFromISR(transmit_done,&woken);return woken==pdTRUE;
}
static void can_setup(void){
    twai_onchip_node_config_t c={.io_cfg={.tx=17,.rx=18,.quanta_clk_out=-1,.bus_off_indicator=-1},.bit_timing={.bitrate=500000},.fail_retry_cnt=0,.tx_queue_depth=1,.intr_priority=2,.flags={.no_receive_rtr=1}};
    ESP_ERROR_CHECK(twai_new_node_onchip(&c,&can));twai_event_callbacks_t callbacks={.on_rx_done=on_rx,.on_tx_done=on_tx};
    ESP_ERROR_CHECK(twai_node_register_event_callbacks(can,&callbacks,NULL));ESP_ERROR_CHECK(twai_node_enable(can));
}
static void can_reset(void){
    twai_node_status_t status;ESP_ERROR_CHECK(twai_node_get_info(can,&status,NULL));
    if(status.state!=TWAI_ERROR_BUS_OFF)ESP_ERROR_CHECK(twai_node_disable(can));
    ESP_ERROR_CHECK(twai_node_delete(can)); /* driver releases queued frame pointers before global buffer reuse */
    xQueueReset(receive_queue);while(xSemaphoreTake(transmit_done,0)==pdTRUE){}
    atomic_store(&rx_overflow,false);can_setup();
}
static bool send8(uint32_t id,const uint8_t *data){
    while(xSemaphoreTake(transmit_done,0)==pdTRUE){}
    memcpy(transmit_bytes,data,8);transmit_frame=(twai_frame_t){.header={.id=id,.dlc=8},.buffer=transmit_bytes,.buffer_len=8};tx_success=false;
    if(twai_node_transmit(can,&transmit_frame,0)!=ESP_OK)return false;
    /* The next call is forbidden after failure until can_reset destroys old TX references. */
    if(xSemaphoreTake(transmit_done,pdMS_TO_TICKS(4))!=pdTRUE || !tx_success)return false;
    return twai_node_transmit_wait_all_done(can,4)==ESP_OK;
}
static bool send64(uint32_t id,uint64_t value){uint8_t p[8];pd_put64(p,value);return send8(id,p);}
#if !CONFIG_PD_EXTERNAL_GATEWAY
static bool acquire(uint64_t sync_us,uint16_t words[9],uint16_t *delay,uint16_t *span){
    uint64_t start=clock_us();for(unsigned i=0;i<pd_port_count[NODE-1];i++)words[i]=read_axis(i);uint64_t end=clock_us();
    if(start<sync_us || end-sync_us>PD_NODE_WINDOW_US || end==start)return false;
    *delay=(uint16_t)(start-sync_us);*span=(uint16_t)(end-start);return true;
}
#endif
#if CONFIG_PD_EXTERNAL_GATEWAY
static void gateway_event(pd_cohort_t *cohort,const rx_event_t *e){
    /* O2 session code owns control frames; no unchallenged legacy ACK. */
    if(e->id>=CAN_END)(void)pd_o_dispatch(cohort,e->id,e->bytes,e->us);
}
static void gateway(void){
    uint8_t mac[6];ESP_ERROR_CHECK(esp_efuse_mac_get_default(mac));uint64_t device=0;for(unsigned i=0;i<6;i++)device=(device<<8)|mac[i];
    pd_cohort_t cohort;pd_init(&cohort,random_id());o2_join_t join={0};
    uint64_t serial_seq=0,next=clock_us(),last_announce=0;rx_event_t e;
    o3_recovery_t recovery;o3_recovery_reset(&recovery);bool missing[6]={true,true,true,true,true,true};
    for(;;){
        sleep_until(next);next+=16667;
        while(xQueueReceive(receive_queue,&e,0)==pdTRUE)gateway_event(&cohort,&e);
        if(atomic_exchange(&rx_overflow,false) || cohort.sequence==UINT32_MAX){
            can_reset();pd_init(&cohort,random_id());last_announce=0;o3_recovery_reset(&recovery);join=(o2_join_t){0};
            for(unsigned i=0;i<6;i++)missing[i]=true;
        }
        bool ok=true;unsigned target=o3_select_maintenance(&recovery,&cohort,missing,clock_us());
        if(!last_announce || clock_us()-last_announce>=100000 || target){ok=send64(CAN_EPOCH,cohort.epoch);last_announce=clock_us();}
        uint64_t start=clock_us();uint32_t seq=cohort.sequence+1;
        if(target && ok){
            /* Dedicated maintenance slot, bounded to one node. No SYNC/data
             * acquisition is requested; USB emits an explicit missing cohort. */
            /* Scheduler already charged this explicit maintenance cohort. */
            uint64_t token=random_id();ok=o2_join_begin(&join,&cohort,target,token);
            if(ok)ok=send64(O2_POLL+target,token);
            bool admitted=false;
            while(ok && clock_us()<start+PD_DEADLINE_US){
                if(xQueueReceive(receive_queue,&e,1)==pdTRUE){
                    bool confirm=false;(void)o2_join_receive(&join,&cohort,e.id,pd_get64(e.bytes),&confirm);
                    if(confirm){ok=send64(O2_JOIN_OK+target,token);admitted=ok;break;}
                }
            }
            if(admitted)missing[target-1]=false;
            o3_join_end(&join,&cohort,admitted);
            ok=ok && pd_begin(&cohort,seq,start);
            for(unsigned i=0;i<6;i++)cohort.node[i].bad=true;
        }else if(ok){
            uint8_t sync[8];pd_put32(sync,seq);pd_put32(sync+4,(uint32_t)start);
            ok=pd_begin(&cohort,seq,start);if(ok)ok=send8(CAN_SYNC,sync);
        }
        if(!ok){
            can_reset();pd_init(&cohort,random_id());last_announce=0;join=(o2_join_t){0};o3_recovery_reset(&recovery);
            for(unsigned i=0;i<6;i++)missing[i]=true;
            start=clock_us();(void)pd_begin(&cohort,1,start);
        }
        while(clock_us()<start+PD_DEADLINE_US){
            if(xQueueReceive(receive_queue,&e,1)==pdTRUE && !target)gateway_event(&cohort,&e);
            if(atomic_load(&rx_overflow))for(unsigned i=0;i<6;i++)cohort.node[i].bad=true;
        }
        while(xQueueReceive(receive_queue,&e,0)==pdTRUE)if(!target)gateway_event(&cohort,&e);
        pd_sample_t sample;if(pd_finish(&cohort,clock_us(),&sample)){
            if(!target){
                for(unsigned i=0;i<6;i++)missing[i]=(sample.presence&(1u<<i))==0;
                o3_observe_sample(&recovery,&sample);
            }
            uint8_t wire[PD_WIRE_MAX];size_t count=pd_encode(&sample,device,boot_id,++serial_seq,wire,sizeof(wire));
            if(count && usb_serial_jtag_is_connected()){
                int sent=usb_serial_jtag_write_bytes(wire,count,0);
                if(sent!=(int)count){uint8_t zero=0;(void)usb_serial_jtag_write_bytes(&zero,1,0);}
            }
        }
        if(clock_us()>next+16667)next=clock_us()+16667;
    }
}
#else
static void regional(void){
    o2_regional_t session;o2_regional_reset(&session);rx_event_t e;
    for(;;){
        bool ok=true;
        if(atomic_exchange(&rx_overflow,false)){can_reset();o2_regional_reset(&session);}
        if(xQueueReceive(receive_queue,&e,pdMS_TO_TICKS(1))!=pdTRUE)continue;
        o2_action_t action=o2_regional_control(&session,NODE,e.id,pd_get64(e.bytes));
        if(action==O2_RESET_EPOCH){can_reset();continue;}
        if(action==O2_REPLY_JOIN){
            /* G0 does not issue SYNC in this dedicated maintenance cohort. */
            ok=send64(O2_BOOT+NODE,boot_id);
            if(ok)ok=send64(O2_JOIN_ACK+NODE,session.challenge ^ boot_id);
        }else if(e.id==CAN_SYNC && o2_regional_sync(&session,pd_get32(e.bytes))){
            uint32_t seq=session.last_seq;
            uint16_t words[9],delay=0,span=0;
            if(!acquire(e.us,words,&delay,&span))continue;
            unsigned count=pd_port_count[NODE-1];uint8_t data[8];pd_put32(data,seq);
            for(unsigned g=0;g<(count+1)/2 && ok;g++){
                pd_put16(data+4,words[2*g]);pd_put16(data+6,2*g+1<count?words[2*g+1]:PD_FIXED);
                ok=send8(CAN_PAIR+NODE*16+g,data);
            }
            if(ok && !atomic_load(&rx_overflow)){pd_put16(data+4,delay);pd_put16(data+6,span);ok=send8(CAN_END+NODE,data);}
        }
        if(!ok){can_reset();o2_regional_reset(&session);vTaskDelay(pdMS_TO_TICKS(20));}
    }
}
#endif
void app_main(void){
    vTaskPrioritySet(NULL,configMAX_PRIORITIES-3);
    boot_id=random_id();receive_queue=xQueueCreate(64,sizeof(rx_event_t));transmit_done=xSemaphoreCreateBinary();configASSERT(receive_queue && transmit_done);
    can_setup();
#if !CONFIG_PD_EXTERNAL_GATEWAY
    spi_setup();
#endif
#if CONFIG_PD_EXTERNAL_GATEWAY
    usb_serial_jtag_driver_config_t usb={.tx_buffer_size=1024,.rx_buffer_size=128};ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));gateway();
#else
    regional();
#endif
}
