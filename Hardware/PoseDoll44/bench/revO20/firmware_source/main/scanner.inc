/* Retained O16 electrical scan order; read-only encoder transactions. */
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
static void fresh_scan(p17_message*m){
 unsigned offset=0;m->valid_mask=0;for(unsigned i=0;i<46;i++)m->words[i]=P17_FAULT;
 for(unsigned chain=0;chain<6;chain++){
  unsigned n=p17_counts[chain];uint16_t rx[6][10]={0};bool io=true;
  for(unsigned b=0;b<6;b++){
   uint16_t w=b<5?p17_command(p17_registers[b]):0;uint8_t tx[20]={0},r[20]={0};
   for(unsigned j=0;j<n;j++){tx[2*j]=(uint8_t)(w>>8);tx[2*j+1]=(uint8_t)w;}
   spi_transaction_t t={.length=n*16,.tx_buffer=tx,.rx_buffer=r};
   gpio_set_level(cs[chain],0);esp_rom_delay_us(2);if(spi_device_polling_transmit(spi,&t)!=ESP_OK)io=false;esp_rom_delay_us(2);gpio_set_level(cs[chain],1);esp_rom_delay_us(2);
   for(unsigned j=0;j<n;j++)rx[b][j]=(uint16_t)(((uint16_t)r[2*j]<<8)|r[2*j+1]);
  }
  if(io){
   bool good=p17_decode_chain(rx,n,m->words+offset);
   // Clear latched AS5048 communication errors for a subsequent new request.
   // Never replace this failed scan with the clearing responses.
   if(!good)for(unsigned b=0;b<2;b++){
    uint16_t w=b==0?p17_command(0x0001):0;uint8_t tx[20]={0},r[20]={0};
    for(unsigned j=0;j<n;j++){tx[2*j]=(uint8_t)(w>>8);tx[2*j+1]=(uint8_t)w;}
    spi_transaction_t t={.length=n*16,.tx_buffer=tx,.rx_buffer=r};
    gpio_set_level(cs[chain],0);esp_rom_delay_us(2);(void)spi_device_polling_transmit(spi,&t);esp_rom_delay_us(2);gpio_set_level(cs[chain],1);esp_rom_delay_us(2);
   }
  }
  for(unsigned j=0;j<n;j++)if(m->words[offset+j]<0x4000)m->valid_mask|=UINT64_C(1)<<(offset+j);
  offset+=n;
 }
}
