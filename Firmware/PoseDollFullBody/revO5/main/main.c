/* Rev O5 request-driven G0 + six A-topology remote nodes. PD41 v1 remains unchanged; no calibration, UDP, IMU or OTP writes.
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
#include "pd41_config.h"
#include "static_gateway.h"
#define PD_FAULT 0x8000
enum { NODE=CONFIG_PD_NODE_ID, IO_FAIL=1, PARITY_FAIL=2, SENSOR_ERROR=4, MAGNET_FAIL=8, NONZERO_OTP=16 };
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

/* Each region request is a CRC-protected datagram with full G0 boot, monotonically
 * increasing token and expected region boot. Old responses cannot complete it. */
enum { O5_QUERY=0x600,O5_REPLY=0x610 };
static bool send_packet(uint32_t id,const uint8_t* raw,size_t bytes,uint64_t deadline)
{
    for(unsigned i=0;i<(bytes+6)/7;i++){
        uint8_t fragment[8];pd5_make_fragment(raw,bytes,i,fragment);
        if(clock_us()>=deadline||!send8(id,fragment)){can_reset();return false;}
    }
    return clock_us()<deadline;
}
#if CONFIG_PD_EXTERNAL_GATEWAY
static uint32_t next_token;
static uint64_t device_id;
static pd5_usb identity,current;
static uint8_t command_buffer[PD5_USB_BYTES];
static size_t command_bytes;
static uint64_t command_started;
static bool active;
static uint64_t next_scan;
static uint8_t seen[32][16];
static unsigned seen_count,seen_next;
static bool output(pd5_usb* msg)
{
    uint8_t wire[PD5_USB_BYTES];pd5_encode_usb(msg,wire);size_t sent=0;uint64_t deadline=clock_us()+20000;
    while(sent<sizeof(wire)&&clock_us()<deadline){int n=usb_serial_jtag_write_bytes(wire+sent,sizeof(wire)-sent,pdMS_TO_TICKS(1));if(n>0)sent+=(size_t)n;}
    return sent==sizeof(wire);
}
static bool query(unsigned node,uint64_t expected,unsigned operation,pd5_region_request* req,pd5_region_result* result,uint64_t deadline)
{
    if(next_token==UINT32_MAX)return false; /* reboot/re-negotiate instead of token wrap */
    *req=(pd5_region_request){.node=(uint8_t)node,.operation=(uint8_t)operation,.gateway_boot=boot_id,.expected_boot=expected,.token=++next_token};
    uint8_t raw[28];pd5_encode_request(req,raw);xQueueReset(receive_queue);atomic_store(&rx_overflow,false);
    if(!send_packet(O5_QUERY+node,raw,sizeof(raw),deadline))return false;
    pd5_fragments fragments={0};rx_event_t event;
    while(clock_us()<deadline){
        if(atomic_exchange(&rx_overflow,false))return false;
        if(xQueueReceive(receive_queue,&event,1)!=pdTRUE)continue;
        if(event.id!=O5_REPLY+node)continue;
        int status=pd5_fragment(&fragments,event.bytes,52,event.us);
        if(status<0)return false;
        if(status==1){
            if(!pd5_decode_result(fragments.data,52,result))return false;
            return result->node==node&&result->gateway_boot==boot_id&&result->token==req->token&&(!expected||result->boot==expected);
        }
    }
    return false;
}
static void discover(void)
{
    active=false;identity=(pd5_usb){.type=PD5_HELLO,.device=device_id,.boot=boot_id};pd5_blank_scan(&identity);
    for(unsigned node=1;node<=6;node++){
        pd5_region_request req;pd5_region_result res;
        if(query(node,0,PD5_PROBE,&req,&res,clock_us()+25000)){
            identity.source_boot[node-1]=res.boot;
            for(unsigned port=0;port<pd_port_count[node-1];port++)if(res.mask&(1u<<port))identity.physical_mask|=UINT64_C(1)<<pd_axis_index[node-1][port];
        }
    }
    (void)output(&identity);
}
static void fail_capture(void){active=false;current.type=PD5_ERROR;(void)output(&current);}
static void accept_command(const pd5_usb* cmd)
{
    if(cmd->type==PD5_PROBE){discover();return;}
    if(cmd->device!=device_id||cmd->boot!=boot_id){fail_capture();return;}
    if(cmd->type==PD5_CANCEL||cmd->type==PD5_STOP){if(!memcmp(cmd->capture,current.capture,16))active=false;return;}
    if(cmd->type!=PD5_REQUEST){fail_capture();return;}
    unsigned nonzero=0;for(unsigned i=0;i<16;i++)nonzero|=cmd->capture[i];
    if(!nonzero){fail_capture();return;}
    if(active&&!memcmp(cmd->capture,current.capture,16)){
        pd5_usb ack=current;ack.type=PD5_ACCEPTED;ack.scan=0;ack.start_us=ack.end_us=0;(void)output(&ack);return;
    }
    for(unsigned i=0;i<seen_count;i++)if(!memcmp(seen[i],cmd->capture,16)){fail_capture();return;}
    memcpy(seen[seen_next],cmd->capture,16);seen_next=(seen_next+1)%32;if(seen_count<32)++seen_count;
    current=identity;current.type=PD5_ACCEPTED;memcpy(current.capture,cmd->capture,16);current.scan=0;
    current.request_us=clock_us();current.start_us=current.end_us=0;active=output(&current);next_scan=clock_us();
}
static void read_commands(void)
{
    uint8_t b;
    if(command_bytes&&clock_us()-command_started>500000){command_bytes=0;fail_capture();}
    for(unsigned budget=0;budget<PD5_USB_BYTES*2;budget++){
        if(usb_serial_jtag_read_bytes(&b,1,0)!=1)break;
        if(command_bytes==0)command_started=clock_us();
        command_buffer[command_bytes++]=b;
        if(command_bytes<=4&&memcmp(command_buffer,"PDG5",command_bytes)){command_bytes=0;fail_capture();continue;}
        if(command_bytes==PD5_USB_BYTES){
            pd5_usb cmd;command_bytes=0;
            if(pd5_decode_usb(command_buffer,sizeof(command_buffer),&cmd))accept_command(&cmd);else fail_capture();
        }
    }
}
static void gateway(void)
{
    uint8_t mac[6];ESP_ERROR_CHECK(esp_efuse_mac_get_default(mac));for(unsigned i=0;i<6;i++)device_id=(device_id<<8)|mac[i];
    current.device=device_id;current.boot=boot_id;
    for(;;){
        read_commands();uint64_t now=clock_us();
        if(active&&(!usb_serial_jtag_is_connected()||now-current.request_us>3000000)){fail_capture();}
        if(active&&now>=next_scan){
            current.type=PD5_SCAN;++current.scan;pd5_blank_scan(&current);current.start_us=clock_us();
            bool complete=true;
            for(unsigned node=1;node<=6;node++){
                pd5_region_request req;pd5_region_result res;uint64_t deadline=clock_us()+20000;
                if(deadline>current.start_us+100000)deadline=current.start_us+100000;
                if(!identity.source_boot[node-1]||!query(node,identity.source_boot[node-1],PD5_REQUEST,&req,&res,deadline)||!pd5_merge_region(&current,&res,&req,clock_us())){complete=false;continue;}
            }
            current.end_us=clock_us();
            /* Missing/invalid regions remain explicit. No retry resets this start time. */
            if(!output(&current))active=false;
            if(!complete)active=false;
            next_scan=current.start_us+100000;
        }
        vTaskDelay(1);
    }
}
#else
static uint16_t read_port(void* unused,unsigned port){(void)unused;return read_axis(port);}
static void regional(void)
{
    pd5_fragments fragments={0};rx_event_t event;uint64_t last_gateway=0;uint32_t last_token=0;
    for(;;){
        if(atomic_exchange(&rx_overflow,false)){can_reset();fragments=(pd5_fragments){0};}
        if(xQueueReceive(receive_queue,&event,1)!=pdTRUE)continue;
        if(event.id!=O5_QUERY+NODE)continue;
        int state=pd5_fragment(&fragments,event.bytes,28,event.us);
        if(state!=1)continue;
        pd5_region_request req;
        if(!pd5_decode_request(fragments.data,28,&req)||req.node!=NODE||(req.expected_boot&&req.expected_boot!=boot_id))continue;
        if(req.gateway_boot==last_gateway&&req.token<=last_token)continue; // A aborts lost datagrams; no cached angle reply.
        last_gateway=req.gateway_boot;last_token=req.token;
        pd5_region_result result={.node=NODE,.count=pd_port_count[NODE-1],.gateway_boot=req.gateway_boot,.boot=boot_id,.token=req.token};
        unsigned ports=CONFIG_PD_BENCH_PORTS;if(ports>result.count)ports=result.count;
        uint64_t start=clock_us();
        if(req.operation==PD5_REQUEST)pd5_acquire_ports(&result,ports,read_port,NULL);
        else{result.mask=(uint16_t)((1u<<ports)-1);for(unsigned i=0;i<9;i++)result.words[i]=PD5_MISSING;}
        result.duration_us=(uint32_t)(clock_us()-start);if(!result.duration_us)result.duration_us=1;
        uint8_t reply[52];if(pd5_encode_result(&result,reply)&&!atomic_load(&rx_overflow))
            (void)send_packet(O5_REPLY+NODE,reply,sizeof(reply),start+100000);
    }
}
#endif
void app_main(void)
{
    vTaskPrioritySet(NULL,configMAX_PRIORITIES-3);boot_id=random_id();
    receive_queue=xQueueCreate(64,sizeof(rx_event_t));transmit_done=xSemaphoreCreateBinary();configASSERT(receive_queue&&transmit_done);can_setup();
#if CONFIG_PD_EXTERNAL_GATEWAY
    usb_serial_jtag_driver_config_t usb={.tx_buffer_size=1024,.rx_buffer_size=1024};ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));gateway();
#else
    spi_setup();regional();
#endif
}
