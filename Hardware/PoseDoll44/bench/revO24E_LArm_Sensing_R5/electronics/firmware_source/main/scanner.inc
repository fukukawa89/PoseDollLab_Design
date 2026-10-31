/* R5: O22 B01/B02/B03/B05/B06/B07 SSI, A01 for the WD TMAG.
 * A01 pin5 (CS_A) is WD SDI. GPIO3 is WD CS_N (10k pull-up to 3V3).
 * While WD is selected, CS_MCU acts as MOSI; unwanted MT read cycles are
 * discarded. No MT register can be written through its SSI output interface.
 * Before each SSI frame restore CS_MCU high for 20 us. MISO paths stay separate.
 */
static const int addr[4]={2,4,5,6},din[3]={8,9,44};
static const int clk=7,csn=43,en=1,wdcs=3;
static bool tm_configured=false;
static uint32_t tm_xfer(uint32_t tx){
 for(unsigned a=0;a<4;a++)gpio_set_level(addr[a],0);
 gpio_set_level(clk,0);gpio_set_level(wdcs,1);esp_rom_delay_us(8);
 tx=(tx&0xfffffff0u)|r5_crc4(tx);uint32_t rx=0;
 gpio_set_level(wdcs,0);esp_rom_delay_us(4);
 for(int bit=31;bit>=0;bit--){
  gpio_set_level(csn,(int)((tx>>bit)&1));esp_rom_delay_us(4);
  gpio_set_level(clk,1);esp_rom_delay_us(4);
  rx=(rx<<1)|(uint32_t)gpio_get_level(din[0]);gpio_set_level(clk,0);
 }
 gpio_set_level(wdcs,1);gpio_set_level(csn,1);esp_rom_delay_us(20);
 return rx;
}
static uint32_t tm_read(unsigned reg,unsigned cmd){return tm_xfer(0x80000000u|(reg<<24)|(cmd<<4));}
static void sensor_setup(void){
 uint64_t mask=(UINT64_C(1)<<en)|(UINT64_C(1)<<clk)|(UINT64_C(1)<<csn)|(UINT64_C(1)<<wdcs);
 for(unsigned i=0;i<4;i++)mask|=UINT64_C(1)<<addr[i];
 gpio_config_t c={.pin_bit_mask=mask,.mode=GPIO_MODE_OUTPUT};ESP_ERROR_CHECK(gpio_config(&c));
 gpio_set_level(en,0);gpio_set_level(wdcs,1);gpio_set_level(csn,1);gpio_set_level(clk,0);
 for(unsigned i=0;i<4;i++)gpio_set_level(addr[i],0);
 c.pin_bit_mask=(UINT64_C(1)<<8)|(UINT64_C(1)<<9)|(UINT64_C(1)<<44);c.mode=GPIO_MODE_INPUT;
 c.pull_up_en=GPIO_PULLUP_DISABLE;c.pull_down_en=GPIO_PULLDOWN_DISABLE;ESP_ERROR_CHECK(gpio_config(&c));
 vTaskDelay(pdMS_TO_TICKS(100));gpio_set_level(en,1);esp_rom_delay_us(20);
 (void)tm_read(13,0);(void)tm_read(14,0); /* acknowledge power-on status once */
 (void)tm_xfer((1u<<24)|(0x01eau<<8)); /* XYZ, all +/-100 mT */
 (void)tm_xfer((2u<<24)); /* regular 16-bit data, command-trigger */
 (void)tm_xfer(0x3130u<<8); /* 8 averages, NdFeB compensation, active trigger */
 uint32_t d=tm_read(0,0),s=tm_read(1,0),y=tm_read(2,0);
 tm_configured=r5_tm_crc_ok(d)&&r5_tm_crc_ok(s)&&r5_tm_crc_ok(y)&&r5_tm_data(d)==0x3130&&r5_tm_data(s)==0x01ea&&r5_tm_data(y)==0;
}
static void fresh_scan(p21_message*m){
 m->valid_mask=0;m->idle_high_mask=0;memset(m->tm,0,sizeof(m->tm));
 for(unsigned i=0;i<46;i++)m->words[i]=P21_FAULT;
 const unsigned slots[6]={0,1,2,4,5,6},raw[6]={12,13,14,16,17,18};
 gpio_set_level(wdcs,1);
 for(unsigned j=0;j<6;j++){
  gpio_set_level(csn,1);gpio_set_level(clk,0);
  for(unsigned a=0;a<4;a++)gpio_set_level(addr[a],(slots[j]>>a)&1u);
  esp_rom_delay_us(20);bool idle=gpio_get_level(din[1])!=0;
  uint32_t w=0;gpio_set_level(csn,0);esp_rom_delay_us(4);
  for(unsigned bit=0;bit<24;bit++){
   gpio_set_level(clk,1);esp_rom_delay_us(4);w=(w<<1)|(uint32_t)gpio_get_level(din[1]);
   gpio_set_level(clk,0);esp_rom_delay_us(4);
  }
  gpio_set_level(csn,1);esp_rom_delay_us(20);unsigned i=raw[j];m->words[i]=w;
  if(idle)m->idle_high_mask|=UINT64_C(1)<<i;
  if(p21_sensor_valid(w,idle))m->valid_mask|=UINT64_C(1)<<i;
 }
 if(!tm_configured)return;
 uint32_t old=tm_read(8,0);(void)tm_read(0,1); /* CMD0 starts exactly one XYZ set */
 esp_rom_delay_us(4000);
 m->tm[3]=tm_read(8,0);
 if(!r5_tm_crc_ok(old)||((r5_tm_data(old)^r5_tm_data(m->tm[3]))&0x70)==0)return;
 m->tm[0]=tm_read(9,0);m->tm[1]=tm_read(10,0);m->tm[2]=tm_read(11,0);
 m->tm[4]=tm_read(8,0);m->tm[5]=tm_read(13,0);m->tm[6]=tm_read(14,0);m->tm[7]=tm_read(0,0);
}
