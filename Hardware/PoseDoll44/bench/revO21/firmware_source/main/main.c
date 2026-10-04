/* O21 prototype only. New SSI carrier required; never flash onto O20 wiring. */
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "driver/usb_serial_jtag.h"
#include "esp_timer.h"
#include "esp_rom_sys.h"
#include "esp_random.h"
#include "esp_mac.h"
#include "esp_err.h"
#include "bootloader_random.h"
#include "raw46.h"
#include "session.h"
static p21_session session;
static uint64_t clock_us(void){return (uint64_t)esp_timer_get_time();}
#include "scanner.inc"
static bool usb_output(const p21_message*m){
 uint8_t bytes[P21_BYTES];if(!p21_encode(m,bytes))return false;size_t sent=0;uint64_t deadline=clock_us()+20000;
 while(sent<sizeof(bytes)&&clock_us()<deadline){int n=usb_serial_jtag_write_bytes(bytes+sent,sizeof(bytes)-sent,1);if(n>0)sent+=(size_t)n;}
 return sent==sizeof(bytes);
}
static void fail(void){p21_message out;p21_session_fail(&session,&out);(void)usb_output(&out);}
void app_main(void){
 // Supply real entropy while radio is deliberately disabled, before SPI setup.
 uint64_t boot=0;bootloader_random_enable();while(!boot)esp_fill_random(&boot,sizeof(boot));bootloader_random_disable();
 uint8_t mac[6];ESP_ERROR_CHECK(esp_read_mac(mac,ESP_MAC_WIFI_STA));uint64_t device=0;for(unsigned i=0;i<6;i++)device=(device<<8)|mac[i];
 p21_session_init(&session,device,boot);
 usb_serial_jtag_driver_config_t usb={.tx_buffer_size=2048,.rx_buffer_size=2048};ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));sensor_setup();
 uint8_t bytes[P21_BYTES];size_t filled=0;uint64_t begun=0;
 for(;;){
  uint8_t b;
  for(unsigned budget=0;budget<P21_BYTES*2;budget++){
   if(usb_serial_jtag_read_bytes(&b,1,0)!=1)break;
   if(!filled){begun=clock_us();}
   bytes[filled++]=b;
   if(filled<=4&&memcmp(bytes,"P21R",filled)){filled=0;fail();continue;}
   if(filled==P21_BYTES){p21_message m,out;filled=0;if(!p21_decode(bytes,sizeof(bytes),&m))fail();else if(p21_session_command(&session,&m,clock_us(),&out)&&!usb_output(&out))fail();}
  }
  if(filled&&clock_us()-begun>500000){filled=0;fail();}
  if(!usb_serial_jtag_is_connected()){
   if(session.active){fail();}
   session.discovered=false;filled=0;
  }else{
   p21_message out;
   if(p21_session_begin(&session,clock_us(),&out)){
    if(out.type==P21_SCAN){fresh_scan(&out);p21_session_complete(&session,&out,clock_us());}
    if(!usb_output(&out))fail();
   }
  }
  vTaskDelay(1);
 }
}
