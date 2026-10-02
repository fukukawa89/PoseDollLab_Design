/* O15-C1 experimental raw46 central scanner + external G0. No OTP writes.
 * Pair MACs explicitly before hardware tests. Default zero MAC cannot pair.
 * G0 start/end bracket radio request+fresh body scan+reply in G0 clock domain.
 * Declared chain lengths never prove physical node count. Commission every node.
 */
#include <stdatomic.h>
#include <string.h>
#include <stdio.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "driver/usb_serial_jtag.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_timer.h"
#include "esp_rom_sys.h"
#include "esp_random.h"
#include "esp_system.h"
#include "esp_mac.h"
#include "esp_err.h"
#include "raw46.h"
static QueueHandle_t radio_rx;
static SemaphoreHandle_t radio_done;
static atomic_bool overflow;
static volatile bool tx_ok;
static uint8_t peer[6],transmit[P15_BYTES];
static bool paired;
static uint64_t boot_id,device;
static uint64_t clock_us(void){return (uint64_t)esp_timer_get_time();}
static uint64_t random_id(void){uint64_t n=0;while(!n)n=((uint64_t)esp_random()<<32)|esp_random();return n;}
static void rx_callback(const esp_now_recv_info_t *info,const uint8_t* data,int n){
 if(!paired||n!=P15_BYTES||memcmp(info->src_addr,peer,6))return;
 if(xQueueSend(radio_rx,data,0)!=pdTRUE)atomic_store(&overflow,true);
}
static void tx_callback(const esp_now_send_info_t *info,esp_now_send_status_t status){(void)info;tx_ok=status==ESP_NOW_SEND_SUCCESS;xSemaphoreGive(radio_done);}
static void radio_setup(void){
 esp_err_t e=nvs_flash_init();if(e==ESP_ERR_NVS_NO_FREE_PAGES||e==ESP_ERR_NVS_NEW_VERSION_FOUND){ESP_ERROR_CHECK(nvs_flash_erase());e=nvs_flash_init();}ESP_ERROR_CHECK(e);
 ESP_ERROR_CHECK(esp_netif_init());ESP_ERROR_CHECK(esp_event_loop_create_default());wifi_init_config_t c=WIFI_INIT_CONFIG_DEFAULT();
 ESP_ERROR_CHECK(esp_wifi_init(&c));ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));ESP_ERROR_CHECK(esp_wifi_start());ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));ESP_ERROR_CHECK(esp_wifi_set_channel(CONFIG_P15_CHANNEL,WIFI_SECOND_CHAN_NONE));
 uint8_t mac[6];ESP_ERROR_CHECK(esp_wifi_get_mac(WIFI_IF_STA,mac));device=0;for(unsigned i=0;i<6;i++)device=(device<<8)|mac[i];
 unsigned p[6]={0};int used=0;const char*s=CONFIG_P15_PEER_MAC;
 if(sscanf(s,"%2x:%2x:%2x:%2x:%2x:%2x%n",p,p+1,p+2,p+3,p+4,p+5,&used)==6&&used==17&&strlen(s)==17){
  unsigned nonzero=0;for(unsigned i=0;i<6;i++){peer[i]=(uint8_t)p[i];nonzero|=p[i];}paired=nonzero&&!(peer[0]&1)&&memcmp(peer,mac,6);
 }
 radio_rx=xQueueCreate(16,P15_BYTES);radio_done=xSemaphoreCreateBinary();configASSERT(radio_rx&&radio_done);
 ESP_ERROR_CHECK(esp_now_init());ESP_ERROR_CHECK(esp_now_register_recv_cb(rx_callback));ESP_ERROR_CHECK(esp_now_register_send_cb(tx_callback));
 if(paired){esp_now_peer_info_t cfg={0};memcpy(cfg.peer_addr,peer,6);cfg.channel=CONFIG_P15_CHANNEL;cfg.ifidx=WIFI_IF_STA;cfg.encrypt=false;ESP_ERROR_CHECK(esp_now_add_peer(&cfg));}
}
static bool send_radio(const p15_message*m){
 if(!paired||!p15_encode(m,transmit))return false;
 while(xSemaphoreTake(radio_done,0)==pdTRUE){}tx_ok=false;
 if(esp_now_send(peer,transmit,sizeof(transmit))!=ESP_OK)return false;
 // A timeout can leave SDK transmission pending. Reboot, never overwrite its buffer.
 if(xSemaphoreTake(radio_done,pdMS_TO_TICKS(60))!=pdTRUE)esp_restart();
 return tx_ok;
}
static bool receive_radio(p15_message*m,uint64_t deadline){
 uint8_t bytes[P15_BYTES];
 while(clock_us()<deadline){
  if(atomic_exchange(&overflow,false))return false;
  if(xQueueReceive(radio_rx,bytes,1)==pdTRUE&&p15_decode(bytes,sizeof(bytes),m))return true;
 }
 return false;
}
#if !CONFIG_P15_GATEWAY
static spi_device_handle_t spi;
static const int cs[6]={2,4,5,6,43,44};
static void sensor_setup(void){
 // GPIO1 enables six branch-local open-drain OE stages. Low means disconnected.
 uint64_t mask=UINT64_C(1)<<1;for(unsigned i=0;i<6;i++)mask|=UINT64_C(1)<<cs[i];
 gpio_config_t c={.pin_bit_mask=mask,.mode=GPIO_MODE_OUTPUT};ESP_ERROR_CHECK(gpio_config(&c));gpio_set_level(1,0);
 for(unsigned i=0;i<6;i++)gpio_set_level(cs[i],1);
 spi_bus_config_t bus={.mosi_io_num=9,.miso_io_num=8,.sclk_io_num=7,.quadwp_io_num=-1,.quadhd_io_num=-1,.max_transfer_sz=20};
 ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST,&bus,SPI_DMA_DISABLED));
 spi_device_interface_config_t dev={.clock_speed_hz=100000,.mode=1,.spics_io_num=-1,.queue_size=1};ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST,&dev,&spi));
 ESP_ERROR_CHECK(gpio_set_pull_mode(8,GPIO_PULLUP_ONLY));vTaskDelay(pdMS_TO_TICKS(50));gpio_set_level(1,1);
}
static void fresh_scan(p15_message*m){
 unsigned offset=0;m->valid_mask=0;for(unsigned i=0;i<46;i++)m->words[i]=P15_FAULT;
 for(unsigned chain=0;chain<6;chain++){
  unsigned n=p15_counts[chain];uint16_t rx[6][10]={0};bool io=true;
  for(unsigned b=0;b<6;b++){
   uint16_t w=b<5?p15_command(p15_registers[b]):0;uint8_t tx[20]={0},r[20]={0};
   for(unsigned j=0;j<n;j++){tx[2*j]=(uint8_t)(w>>8);tx[2*j+1]=(uint8_t)w;}
   spi_transaction_t t={.length=n*16,.tx_buffer=tx,.rx_buffer=r};
   gpio_set_level(cs[chain],0);esp_rom_delay_us(2);if(spi_device_polling_transmit(spi,&t)!=ESP_OK)io=false;esp_rom_delay_us(2);gpio_set_level(cs[chain],1);esp_rom_delay_us(2);
   for(unsigned j=0;j<n;j++)rx[b][j]=(uint16_t)(((uint16_t)r[2*j]<<8)|r[2*j+1]);
  }
  if(io){
   bool good=p15_decode_chain(rx,n,m->words+offset);
   // Clear latched AS5048 communication errors for a subsequent new request.
   // Never replace this failed scan with the clearing responses.
   if(!good)for(unsigned b=0;b<2;b++){
    uint16_t w=b==0?p15_command(0x0001):0;uint8_t tx[20]={0},r[20]={0};
    for(unsigned j=0;j<n;j++){tx[2*j]=(uint8_t)(w>>8);tx[2*j+1]=(uint8_t)w;}
    spi_transaction_t t={.length=n*16,.tx_buffer=tx,.rx_buffer=r};
    gpio_set_level(cs[chain],0);esp_rom_delay_us(2);(void)spi_device_polling_transmit(spi,&t);esp_rom_delay_us(2);gpio_set_level(cs[chain],1);esp_rom_delay_us(2);
   }
  }
  for(unsigned j=0;j<n;j++)if(m->words[offset+j]<0x4000)m->valid_mask|=UINT64_C(1)<<(offset+j);
  offset+=n;
 }
}
static void body(void){
 sensor_setup();uint64_t bound=0;uint32_t last=0;
 for(;;){
  p15_message m;if(!receive_radio(&m,clock_us()+100000))continue;
  if(m.device!=device)continue; // bind calibration to the physical body MAC
  if(m.type==P15_PROBE){
   if(!m.gateway_boot)continue;
   if(bound!=m.gateway_boot){bound=m.gateway_boot;last=0;}
   m.type=P15_HELLO;m.body_boot=boot_id;m.valid_mask=0;(void)send_radio(&m);continue;
  }
  if(m.type!=P15_READ||!bound||m.gateway_boot!=bound||m.body_boot!=boot_id||!m.token||m.token<=last||!m.scan)continue;
  last=m.token;m.type=P15_BODY_SCAN;m.start_us=clock_us();fresh_scan(&m);m.end_us=clock_us();(void)send_radio(&m);
 }
}
#else
static p15_message identity,current;
static uint32_t token;
static bool active;
static uint64_t next_scan;
static uint8_t retired[4096][16];static unsigned retired_count;
static bool usb_output(p15_message*m){
 uint8_t bytes[P15_BYTES];if(!p15_encode(m,bytes))return false;size_t sent=0;uint64_t deadline=clock_us()+20000;
 while(sent<sizeof(bytes)&&clock_us()<deadline){int n=usb_serial_jtag_write_bytes(bytes+sent,sizeof(bytes)-sent,1);if(n>0)sent+=(size_t)n;}
 return sent==sizeof(bytes);
}
static void fail(void){active=false;current.type=P15_ERROR;(void)usb_output(&current);}
static bool exchange(p15_message*q,p15_message*r,uint64_t deadline){
 xQueueReset(radio_rx);atomic_store(&overflow,false);if(!send_radio(q))return false;
 while(receive_radio(r,deadline)){
  if(r->device!=q->device||r->gateway_boot!=boot_id)continue;
  if(q->type==P15_PROBE&&r->type==P15_HELLO&&r->body_boot)return true;
  if(r->type==P15_BODY_SCAN&&r->body_boot==q->body_boot&&r->scan==q->scan&&r->token==q->token&&!memcmp(r->capture,q->capture,16)&&r->end_us>r->start_us&&r->end_us-r->start_us<=100000)return true;
 }
 return false;
}
static void discover(void){
 active=false;identity=(p15_message){.type=P15_PROBE,.device=device,.gateway_boot=boot_id};p15_message reply;
 if(!exchange(&identity,&reply,clock_us()+150000)){current=identity;fail();return;}
 identity.type=P15_HELLO;identity.body_boot=reply.body_boot;identity.valid_mask=0;current=identity;(void)usb_output(&identity);
}
static void command(const p15_message*m){
 if(m->type==P15_PROBE){discover();return;}
 if(m->device!=device||m->gateway_boot!=boot_id||!identity.body_boot||m->body_boot!=identity.body_boot){fail();return;}
 if(m->type==P15_CANCEL||m->type==P15_STOP){if(!memcmp(m->capture,current.capture,16))active=false;return;}
 if(m->type!=P15_REQUEST){fail();return;}
 unsigned nz=0;for(unsigned i=0;i<16;i++)nz|=m->capture[i];if(!nz){fail();return;}
 if(active&&!memcmp(m->capture,current.capture,16)){p15_message ack=current;ack.type=P15_ACCEPTED;ack.scan=0;ack.start_us=ack.end_us=0;(void)usb_output(&ack);return;}
 for(unsigned i=0;i<retired_count;i++)if(!memcmp(m->capture,retired[i],16)){fail();return;}
 if(retired_count==4096){fail();return;}
 memcpy(retired[retired_count++],m->capture,16);
 current=identity;current.type=P15_ACCEPTED;memcpy(current.capture,m->capture,16);current.request_us=clock_us();current.scan=0;current.valid_mask=0;current.start_us=current.end_us=0;active=usb_output(&current);next_scan=clock_us();
}
static void gateway(void){
 uint8_t bytes[P15_BYTES];size_t filled=0;uint64_t begun=0;
 for(;;){
  uint8_t b;
  for(unsigned budget=0;budget<P15_BYTES*2;budget++){
   if(usb_serial_jtag_read_bytes(&b,1,0)!=1)break;
   if(!filled){begun=clock_us();}
   bytes[filled++]=b;
   if(filled<=4&&memcmp(bytes,"P15R",filled)){filled=0;fail();continue;}
   if(filled==P15_BYTES){p15_message m;filled=0;if(p15_decode(bytes,sizeof(bytes),&m))command(&m);else fail();}
  }
  if(filled&&clock_us()-begun>500000){filled=0;fail();}
  uint64_t now=clock_us();
  if(active&&(!usb_serial_jtag_is_connected()||now-current.request_us>3000000))fail();
  if(active&&now>=next_scan){
   if(token==UINT32_MAX){fail();continue;}
   p15_message q=current,result;q.type=P15_READ;q.scan=++current.scan;q.token=++token;q.start_us=clock_us();
   if(!exchange(&q,&result,q.start_us+100000)){fail();continue;}
   uint64_t end=clock_us();if(end-q.start_us>100000){fail();continue;}
   result.type=P15_SCAN;result.request_us=current.request_us;result.start_us=q.start_us;result.end_us=end;
   current.token=q.token;current.scan=q.scan;current.start_us=q.start_us;current.end_us=end;current.valid_mask=result.valid_mask;memcpy(current.words,result.words,sizeof(current.words));current.type=P15_SCAN;
   if(!usb_output(&current)||current.valid_mask!=P15_MASK)active=false;
   next_scan=q.start_us+100000;
  }
  vTaskDelay(1);
 }
}
#endif
void app_main(void){
 boot_id=random_id();usb_serial_jtag_driver_config_t usb={.tx_buffer_size=2048,.rx_buffer_size=2048};ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));radio_setup();
#if CONFIG_P15_GATEWAY
 // The device identity is the paired physical body, not the replaceable G0.
 device=0;for(unsigned i=0;i<6;i++)device=(device<<8)|peer[i];
 gateway();
#else
 body();
#endif
}
