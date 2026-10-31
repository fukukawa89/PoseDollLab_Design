/* SSI candidate: Mode-1 style bit sampling, validated in software only.
 * Mainboard buffers CLK/CSN separately per bank. DO pins never connect together.
 * All sensors in a bank receive CSN/CLK; mux selects only which DO we observe.
 * The CTS timing/CRC and idle-high behavior need a real waveform qualification.
 */
static const int addr[4]={2,4,5,6},din[3]={8,9,44};
static const int clk=7,csn=43,en=1;
static const int raw_index[3][16]={
{0,1,2,3,4,5,6,7,8,9,10,11,20,21,-1,-1},
{12,13,14,15,16,17,18,19,22,23,24,25,26,27,28,29},
{30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45}
};
static void sensor_setup(void){
 uint64_t mask=(UINT64_C(1)<<en)|(UINT64_C(1)<<clk)|(UINT64_C(1)<<csn);
 for(unsigned i=0;i<4;i++)mask|=UINT64_C(1)<<addr[i];
 gpio_config_t c={.pin_bit_mask=mask,.mode=GPIO_MODE_OUTPUT};ESP_ERROR_CHECK(gpio_config(&c));
 gpio_set_level(en,0);gpio_set_level(csn,1);gpio_set_level(clk,0);
 for(unsigned i=0;i<4;i++)gpio_set_level(addr[i],0);
 c.pin_bit_mask=(UINT64_C(1)<<8)|(UINT64_C(1)<<9)|(UINT64_C(1)<<44);c.mode=GPIO_MODE_INPUT;c.pull_up_en=GPIO_PULLUP_DISABLE;c.pull_down_en=GPIO_PULLDOWN_DISABLE;
 ESP_ERROR_CHECK(gpio_config(&c));
 vTaskDelay(pdMS_TO_TICKS(100));gpio_set_level(en,1);
}
static void fresh_scan(p21_message*m){
 m->valid_mask=0;m->idle_high_mask=0;
 for(unsigned i=0;i<46;i++)m->words[i]=P21_FAULT;
 for(unsigned slot=0;slot<16;slot++){
  gpio_set_level(csn,1);gpio_set_level(clk,0);
  for(unsigned a=0;a<4;a++)gpio_set_level(addr[a],(int)((slot>>a)&1u));
  esp_rom_delay_us(20);
  bool idle[3];for(unsigned b=0;b<3;b++)idle[b]=gpio_get_level(din[b])!=0;
  uint32_t w[3]={0,0,0};gpio_set_level(csn,0);esp_rom_delay_us(20);
  for(unsigned bit=0;bit<24;bit++){
   gpio_set_level(clk,1);esp_rom_delay_us(20);
   for(unsigned b=0;b<3;b++)w[b]=(w[b]<<1)|(uint32_t)gpio_get_level(din[b]);
   gpio_set_level(clk,0);esp_rom_delay_us(20);
  }
  gpio_set_level(csn,1);esp_rom_delay_us(20);
  for(unsigned b=0;b<3;b++){
   int i=raw_index[b][slot];if(i<0)continue;
   m->words[i]=w[b];
   if(idle[b])m->idle_high_mask|=UINT64_C(1)<<i;
   if(p21_sensor_valid(w[b],idle[b]))m->valid_mask|=UINT64_C(1)<<i;
  }
 }
}
