/*

  HelloWorld.ino

  Universal 8bit Graphics Library (https://github.com/olikraus/u8g2/)

  Copyright (c) 2016, olikraus@gmail.com
  All rights reserved.

  Redistribution and use in source and binary forms, with or without modification, 
  are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice, this list 
    of conditions and the following disclaimer.
    
  * Redistributions in binary form must reproduce the above copyright notice, this 
    list of conditions and the following disclaimer in the documentation and/or other 
    materials provided with the distribution.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
  CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
  MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT 
  NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  

*/

#include <Arduino.h>
#include <U8g2lib.h>

#ifdef U8X8_HAVE_HW_SPI
#include <SPI.h>
#endif
#ifdef U8X8_HAVE_HW_I2C
#include <Wire.h>
#endif

/*
  U8glib Example Overview:
    Frame Buffer Examples: clearBuffer/sendBuffer. Fast, but may not work with all Arduino boards because of RAM consumption
    Page Buffer Examples: firstPage/nextPage. Less RAM usage, should work with all Arduino boards.
    U8x8 Text Only Example: No RAM usage, direct communication with display controller. No graphics, 8x8 Text only.
    
*/

#define asdex_logo_width 57
#define asdex_logo_height 62


static const unsigned char asdex[] U8X8_PROGMEM = {
   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x07,
   0x00, 0x00, 0x00, 0x00, 0x00, 0xe0, 0x00, 0x7c, 0x00, 0x00, 0x00, 0x00,
   0x00, 0x18, 0x00, 0xc0, 0x03, 0x00, 0x00, 0x00, 0x00, 0x07, 0xf8, 0x00,
   0x0e, 0x00, 0x00, 0x00, 0x80, 0x81, 0x9f, 0x0f, 0x38, 0x00, 0x00, 0x00,
   0x40, 0xc0, 0x01, 0xfe, 0x60, 0x00, 0x00, 0x00, 0x20, 0x60, 0x00, 0xc0,
   0x81, 0x01, 0x00, 0x00, 0x10, 0x38, 0x00, 0x80, 0x06, 0x06, 0x00, 0x00,
   0x08, 0x1c, 0x00, 0x00, 0x0d, 0x0c, 0x00, 0x00, 0x08, 0x0e, 0x00, 0x00,
   0x7e, 0x10, 0x00, 0x00, 0x84, 0x07, 0x00, 0x00, 0xfc, 0x20, 0x00, 0x00,
   0x84, 0x07, 0x00, 0x00, 0x1c, 0xc1, 0x00, 0x00, 0x04, 0x03, 0x00, 0x00,
   0x78, 0x82, 0x01, 0x00, 0x04, 0x03, 0x00, 0x00, 0xf0, 0x04, 0x03, 0x00,
   0x84, 0x01, 0x00, 0x00, 0xe0, 0x09, 0x02, 0x00, 0x84, 0x01, 0x00, 0x00,
   0xc0, 0x13, 0x04, 0x00, 0x82, 0x00, 0x00, 0x00, 0x80, 0x27, 0x08, 0x00,
   0xc2, 0x00, 0x00, 0x00, 0x00, 0x7f, 0x18, 0x00, 0x42, 0x00, 0x00, 0x00,
   0x00, 0x3e, 0x10, 0x00, 0x42, 0x00, 0x00, 0x00, 0x00, 0x06, 0x20, 0x00,
   0x62, 0x00, 0x00, 0x00, 0x00, 0x04, 0x20, 0x00, 0x62, 0x00, 0x00, 0x00,
   0x00, 0x08, 0x40, 0x00, 0x22, 0x00, 0x00, 0x00, 0x00, 0x10, 0x40, 0x00,
   0x22, 0x00, 0x00, 0x00, 0x00, 0x10, 0x40, 0x00, 0x32, 0x00, 0x00, 0x00,
   0x00, 0x10, 0x80, 0x00, 0x32, 0x00, 0x00, 0x00, 0x00, 0x30, 0x80, 0x00,
   0x32, 0x00, 0x00, 0x00, 0x00, 0x20, 0x80, 0x00, 0x32, 0x00, 0x00, 0x00,
   0x00, 0x20, 0x80, 0x00, 0x12, 0x00, 0x00, 0x00, 0x00, 0x20, 0x80, 0x00,
   0x12, 0x00, 0x00, 0x00, 0x00, 0x20, 0x80, 0x00, 0x12, 0x00, 0x00, 0x00,
   0x00, 0x10, 0x80, 0x00, 0x12, 0x00, 0x00, 0x00, 0x00, 0x10, 0x80, 0x00,
   0x12, 0x00, 0x00, 0x00, 0x00, 0x10, 0x80, 0x00, 0x32, 0x00, 0x00, 0x00,
   0x00, 0x10, 0x80, 0x00, 0x32, 0x00, 0x00, 0x00, 0x00, 0x08, 0x80, 0x00,
   0x32, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x80, 0x00, 0x32, 0x00, 0x00, 0x00,
   0x00, 0x04, 0x80, 0x00, 0x22, 0x00, 0x00, 0x00, 0x00, 0x06, 0x40, 0x00,
   0x22, 0x00, 0x00, 0x00, 0x00, 0x03, 0x40, 0x00, 0x62, 0x00, 0x00, 0x00,
   0x80, 0x01, 0x40, 0x00, 0x62, 0x00, 0x00, 0x00, 0xc0, 0x00, 0x20, 0x00,
   0x62, 0x00, 0x00, 0x00, 0x60, 0x00, 0x30, 0x00, 0xc2, 0x00, 0x00, 0x00,
   0xe0, 0x0f, 0x10, 0x00, 0xc2, 0x00, 0x00, 0x00, 0xb0, 0x0f, 0x18, 0x00,
   0x02, 0x00, 0x00, 0x00, 0xbc, 0x04, 0x0c, 0x00, 0xe4, 0x01, 0x00, 0x00,
   0x76, 0x03, 0x04, 0x00, 0x7c, 0x03, 0x00, 0x80, 0xbd, 0x01, 0x02, 0x00,
   0x64, 0x06, 0x00, 0xc0, 0xdf, 0x00, 0x01, 0x00, 0x04, 0x1c, 0x00, 0xe0,
   0x25, 0x80, 0x01, 0x00, 0x04, 0x18, 0x00, 0x78, 0x1e, 0x40, 0x00, 0x00,
   0x04, 0x28, 0x00, 0x1c, 0x00, 0x20, 0x00, 0x00, 0x08, 0x28, 0x00, 0x0e,
   0x00, 0x18, 0x00, 0x00, 0x18, 0x38, 0x00, 0x06, 0x00, 0x0c, 0x00, 0x00,
   0x10, 0x18, 0x00, 0x03, 0x00, 0x03, 0x00, 0x00, 0x20, 0xf8, 0x1f, 0x03,
   0x80, 0x01, 0x00, 0x00, 0xc0, 0x6c, 0x38, 0x01, 0x60, 0x00, 0x00, 0x00,
   0x80, 0x09, 0xf0, 0x01, 0x18, 0x00, 0x00, 0x00, 0x00, 0x06, 0xc0, 0x00,
   0x0e, 0x00, 0x00, 0x00, 0x00, 0x78, 0x00, 0xc0, 0x03, 0x00, 0x00, 0x00,
   0x00, 0xc0, 0x0f, 0x7e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0x03,
   0x00, 0x00, 0x00, 0x00};

const u8g2_uint_t F[]={18, 55, 55, 27, 55, 24, 53, 21, 52, 18, 47, 18, 42, 18, 39, 15, 36,
       11, 32,  8, 27,  6, 22,  4, 17,  6, 12,  9,  9, 15,  7, 21,  6, 26,
        5, 30,  6, 35};

const u8g2_uint_t G[] ={18, 55, 56, 29, 55, 27, 55, 24, 53, 21, 52, 18, 46, 19, 42, 18, 39,
       15, 36, 11, 32,  7, 27,  6, 22,  4, 17,  6, 12, 10,  9, 15,  7, 21,
        6, 26,  5, 30,  6, 35,  7, 39};

const u8g2_uint_t H1[] ={48, 38, 43, 18, 39, 15, 34,  9, 28,  6, 23,  4, 19,  5, 16,  6, 13,
        8, 11, 10};

const u8g2_uint_t H2[] ={48, 38, 21,  4, 18,  5, 15,  7, 12,  9, 11, 11,  9, 14,  8, 16,  7,
       19,  7, 21,  6, 23,  6, 26,  5, 28,  5, 30,  5, 31,  6, 33};

const u8g2_uint_t H3[] ={48, 38,  6, 27,  5, 28,  5, 30,  5, 32,  5, 34,  6, 36,  6, 38,  7,
       40,  7, 42,  7, 44,  9, 45, 10, 47, 12, 48, 13, 49, 14, 51};

const u8g2_uint_t I1[] = {49, 30, 28,  6, 23,  5, 19,  5 };

const u8g2_uint_t I2[] = {49, 30, 13,  8, 12,  9, 11, 11, 10, 12,  9, 14,  8, 16,  7, 18,  7,
       20,  6, 22,  6, 24,  6, 26,  5, 28,  5, 30,  5, 32,  6, 34,  6, 36,
        6, 37,  6, 39,  7, 41,  7, 42,  3, 45,  8, 45};

const u8g2_uint_t I3[] = {49, 30, 11, 48, 13, 49, 14, 52, 15, 54, 19, 54};

const u8g2_uint_t J1[] = {48, 22, 15,  7, 13,  8, 11, 10, 10, 11,  3, 12,  8, 15,  8, 17,  7,
       19,  7, 20,  6, 22,  6, 24,  5, 26,  5, 28,  5, 30,  5, 31,  5, 33};

const u8g2_uint_t J2[] = {48, 22,  6, 23,  6, 25,  6, 26,  5, 28,  5, 31,  5, 33,  6, 35,  6,
       37,  7, 39,  7, 42,  7, 46, 10, 46, 12, 49, 14, 51, 14, 54};

const u8g2_uint_t J3[] = {48, 22,  7, 42,  3, 47, 11, 47, 13, 49, 14, 52, 17, 54, 21, 55, 30,
       47, 34, 46, 38, 45};

const u8g2_uint_t K1[] = {35,  9,  6, 22,  6, 24,  5, 26,  5, 29,  5, 32,  6, 35,  6, 39,  7,
       43,  9, 46, 12, 49, 13, 55, 18, 54};
       
const u8g2_uint_t K2[] = {35,  9,  6, 35,  6, 37,  7, 41,  8, 45, 11, 48, 14, 50, 17, 54, 22,
       56, 28, 49, 33, 47, 37, 46, 40, 43, 43, 43};
       
const u8g2_uint_t L[] = {8, 14, 12, 49, 16, 54, 20, 54, 24, 56, 26, 51, 29, 49, 32, 47, 36,
       47, 38, 44, 41, 42, 50, 45, 52, 42, 53, 39, 53, 36, 54, 34, 55, 31,
       56, 29};
       
const u8g2_uint_t M[] = {7, 43, 53, 40, 53, 38, 54, 36, 54, 34, 55, 31, 56, 28, 55, 26, 54,
       23, 53, 20, 52, 18, 45, 18, 42, 17, 40, 16, 38, 14, 36, 12, 34, 10,
       33,  8, 31,  6};
       
const u8g2_uint_t T[] = {49, 30,  5, 28,  5, 28,  5, 29,  5, 29,  5, 29,  5, 29,  5, 30,  5,
       30,  5, 30,  5, 31,  5, 31,  5, 31,  5, 31,  5, 32,  5, 32,  5, 32};

uint8_t arrayVal = 0;


//const char* names[] PROGMEM = {"F", "G", "H1", "H2", "H3", "I1", "I2", "I3", "J1", "J2", "J3", "K1", "K2", "L", "M", "T"};
    
   
// Please UNCOMMENT one of the contructor lines below
// U8g2 Contructor List (Frame Buffer)
// The complete list is available here: https://github.com/olikraus/u8g2/wiki/u8g2setupcpp
// Please update the pin numbers according to your setup. Use U8X8_PIN_NONE if the reset pin is not connected
//U8G2_SSD1306_128X64_NONAME_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_SSD1306_128X64_NONAME_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 12, /* dc=*/ 4, /* reset=*/ 6);	// Arduboy (Production, Kickstarter Edition)
//U8G2_SSD1306_128X64_NONAME_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_SSD1306_128X64_NONAME_F_3W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* reset=*/ 8);
//U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);
//U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* reset=*/ 8);
//U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ SCL, /* data=*/ SDA, /* reset=*/ U8X8_PIN_NONE);   // All Boards without Reset of the Display
//U8G2_SSD1306_128X64_NONAME_F_6800 u8g2(U8G2_R0, 13, 11, 2, 3, 4, 5, 6, A4, /*enable=*/ 7, /*cs=*/ 10, /*dc=*/ 9, /*reset=*/ 8);
//U8G2_SSD1306_128X64_NONAME_F_8080 u8g2(U8G2_R0, 13, 11, 2, 3, 4, 5, 6, A4, /*enable=*/ 7, /*cs=*/ 10, /*dc=*/ 9, /*reset=*/ 8);
//U8G2_SSD1306_128X64_VCOMH0_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);	// same as the NONAME variant, but maximizes setContrast() range
//U8G2_SH1106_128X64_NONAME_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_SH1106_128X64_VCOMH0_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);		// same as the NONAME variant, but maximizes setContrast() range
//U8G2_SSD1306_128X32_UNIVISION_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ 21, /* data=*/ 20, /* reset=*/ U8X8_PIN_NONE);   // Adafruit Feather M0 Basic Proto + FeatherWing OLED
//U8G2_SSD1306_128X32_UNIVISION_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ SCL, /* data=*/ SDA, /* reset=*/ U8X8_PIN_NONE);   // Adafruit Feather ESP8266/32u4 Boards + FeatherWing OLED
//U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);  // Adafruit ESP8266/32u4/ARM Boards + FeatherWing OLED
//U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE, /* clock=*/ SCL, /* data=*/ SDA);   // pin remapping with ESP8266 HW I2C
//U8G2_SSD1306_64X48_ER_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);   // EastRising 0.66" OLED breakout board, Uno: A4=SDA, A5=SCL, 5V powered
//U8G2_SSD1322_NHD_256X64_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);	// Enable U8G2_16BIT in u8g2.h
//U8G2_SSD1322_NHD_256X64_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);	// Enable U8G2_16BIT in u8g2.h
//U8G2_SSD1325_NHD_128X64_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8); 
//U8G2_SSD1325_NHD_128X64_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);	
//U8G2_SSD1327_SEEED_96X96_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ SCL, /* data=*/ SDA, /* reset=*/ U8X8_PIN_NONE);	// Seeedstudio Grove OLED 96x96
//U8G2_SSD1327_SEEED_96X96_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);	// Seeedstudio Grove OLED 96x96
//U8G2_SSD1329_128X96_NONAME_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_SSD1329_128X96_NONAME_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_SSD1305_128X32_NONAME_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_SSD1305_128X32_NONAME_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_SSD1309_128X64_NONAME0_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  
//U8G2_SSD1309_128X64_NONAME0_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  
//U8G2_SSD1309_128X64_NONAME2_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  
//U8G2_SSD1309_128X64_NONAME2_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  
//U8G2_LD7032_60X32_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 11, /* data=*/ 12, /* cs=*/ 9, /* dc=*/ 10, /* reset=*/ 8);	// SW SPI Nano Board
//U8G2_LD7032_60X32_F_4W_SW_I2C u8g2(U8G2_R0, /* clock=*/ 11, /* data=*/ 12, /* reset=*/ U8X8_PIN_NONE);	// NOT TESTED!
//U8G2_UC1701_EA_DOGS102_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_UC1701_EA_DOGS102_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_PCD8544_84X48_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  // Nokia 5110 Display
//U8G2_PCD8544_84X48_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8); 		// Nokia 5110 Display
//U8G2_PCF8812_96X65_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);	// Could be also PCF8814
//U8G2_PCF8812_96X65_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);						// Could be also PCF8814
//U8G2_KS0108_128X64_F u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 18, /*dc=*/ 17, /*cs0=*/ 14, /*cs1=*/ 15, /*cs2=*/ U8X8_PIN_NONE, /* reset=*/  U8X8_PIN_NONE); 	// Set R/W to low!
//U8G2_KS0108_ERM19264_F u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 18, /*dc=*/ 17, /*cs0=*/ 14, /*cs1=*/ 15, /*cs2=*/ 16, /* reset=*/  U8X8_PIN_NONE); 	// Set R/W to low!
//U8G2_ST7920_192X32_F_8080 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 18, /*cs=*/ U8X8_PIN_NONE, /*dc=*/ 17, /*reset=*/ U8X8_PIN_NONE);
//U8G2_ST7920_192X32_F_SW_SPI u8g2(U8G2_R0, /* clock=*/ 18 /* A4 */ , /* data=*/ 16 /* A2 */, /* CS=*/ 17 /* A3 */, /* reset=*/ U8X8_PIN_NONE);
//U8G2_ST7920_128X64_F_8080 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 18 /* A4 */, /*cs=*/ U8X8_PIN_NONE, /*dc/rs=*/ 17 /* A3 */, /*reset=*/ 15 /* A1 */);	// Remember to set R/W to 0 
//U8G2_ST7920_128X64_F_SW_SPI u8g2(U8G2_R0, /* clock=*/ 18 /* A4 */ , /* data=*/ 16 /* A2 */, /* CS=*/ 17 /* A3 */, /* reset=*/ U8X8_PIN_NONE);
//U8G2_ST7920_128X64_F_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* CS=*/ 10, /* reset=*/ 8);
//U8G2_ST7920_128X64_F_HW_SPI u8g2(U8G2_R0, /* CS=*/ 10, /* reset=*/ 8);
//U8G2_ST7565_EA_DOGM128_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_EA_DOGM128_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_EA_DOGM132_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ U8X8_PIN_NONE);	// DOGM132 Shield
//U8G2_ST7565_EA_DOGM132_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ U8X8_PIN_NONE);	// DOGM132 Shield
//U8G2_ST7565_ZOLEN_128X64_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_ZOLEN_128X64_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_LM6059_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);		// Adafruit ST7565 GLCD
//U8G2_ST7565_LM6059_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);		// Adafruit ST7565 GLCD
//U8G2_ST7565_ERC12864_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_ERC12864_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_NHD_C12832_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_NHD_C12832_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_NHD_C12864_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7565_NHD_C12864_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_ST7567_PI_132X64_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 7, /* dc=*/ 9, /* reset=*/ 8);  // Pax Instruments Shield, LCD_BL=6
//U8G2_ST7567_PI_132X64_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 7, /* dc=*/ 9, /* reset=*/ 8);  // Pax Instruments Shield, LCD_BL=6
//U8G2_NT7534_TG12864R_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  
//U8G2_NT7534_TG12864R_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  
//U8G2_ST7588_JLX12864_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ SCL, /* data=*/ SDA, /* reset=*/ 5);  
//U8G2_ST7588_JLX12864_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ 5);
//U8G2_IST3020_ERC19264_F_6800 u8g2(U8G2_R0, 44, 43, 42, 41, 40, 39, 38, 37,  /*enable=*/ 28, /*cs=*/ 32, /*dc=*/ 30, /*reset=*/ 31); // Connect WR pin with GND
//U8G2_IST3020_ERC19264_F_8080 u8g2(U8G2_R0, 44, 43, 42, 41, 40, 39, 38, 37,  /*enable=*/ 29, /*cs=*/ 32, /*dc=*/ 30, /*reset=*/ 31); // Connect RD pin with 3.3V
//U8G2_IST3020_ERC19264_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);
//U8G2_LC7981_160X80_F_6800 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 18, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // Connect RW with GND
//U8G2_LC7981_160X160_F_6800 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 18, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // Connect RW with GND
//U8G2_LC7981_240X128_F_6800 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 18, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // Connect RW with GND
//U8G2_T6963_240X128_F_8080 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 17, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // Connect RD with +5V, FS0 and FS1 with GND
//U8G2_T6963_256X64_F_8080 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 17, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // Connect RD with +5V, FS0 and FS1 with GND
//U8G2_SED1330_240X128_F_8080 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 17, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // Connect RD with +5V, FG with GND
//U8G2_SED1330_240X128_F_6800 u8g2(U8G2_R0, 13, 11, 2, 3, 4, 5, 6, A4, /*enable=*/ 7, /*cs=*/ 10, /*dc=*/ 9, /*reset=*/ 8); // A0 is dc pin!
//U8G2_RA8835_NHD_240X128_F_8080 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7, /*enable=*/ 17, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // Connect /RD = E with +5V, enable is /WR = RW, FG with GND, 14=Uno Pin A0
//U8G2_RA8835_NHD_240X128_F_6800 u8g2(U8G2_R0, 8, 9, 10, 11, 4, 5, 6, 7,  /*enable=*/ 17, /*cs=*/ 14, /*dc=*/ 15, /*reset=*/ 16); // A0 is dc pin, /WR = RW = GND, enable is /RD = E
//U8G2_UC1604_JLX19264_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8); 
//U8G2_UC1604_JLX19264_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  
//U8G2_UC1608_ERC24064_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  // SW SPI, Due ERC2406465 Test Setup
//U8G2_UC1608_240X128_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);  // SW SPI, Due ERC24064-1 Test Setup
//U8G2_UC1610_EA_DOGXL160_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/  U8X8_PIN_NONE);
//U8G2_UC1610_EA_DOGXL160_F_4W_HW_SPI u8g2(U8G2_R0, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/  U8X8_PIN_NONE);
//U8G2_UC1611_EA_DOGM240_F_2ND_HW_I2C u8g2(U8G2_R0, /* reset=*/ 8);	// Due, 2nd I2C, DOGM240 Test Board
//U8G2_UC1611_EA_DOGM240_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);   // Due, SW SPI, DOGXL240 Test Board
//U8G2_UC1611_EA_DOGXL240_F_2ND_HW_I2C u8g2(U8G2_R0, /* reset=*/ 8);	// Due, 2nd I2C, DOGXL240 Test Board
//U8G2_UC1611_EA_DOGXL240_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);   // Due, SW SPI, DOGXL240 Test Board
//U8G2_SSD1606_172X72_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);		// eInk/ePaper Display
//U8G2_SSD1607_200X200_F_4W_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* cs=*/ 10, /* dc=*/ 9, /* reset=*/ 8);	// eInk/ePaper Display

// End of constructor list

U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ SCL, /* data=*/ SDA, /* reset=*/ U8X8_PIN_NONE);  

void setup(void) {
  pinMode(7, INPUT); 
  digitalWrite(7, HIGH);

  pinMode(6, OUTPUT);
  digitalWrite(6, HIGH);
  u8g2.begin();
}

void loop(void) {
  int j;
  u8g2.clearBuffer();					// clear the internal memory
  u8g2.setFlipMode(1);
  u8g2.setFontMode(1);  /* activate transparent font mode */
  u8g2.setDrawColor(1); /* color 1 for the box */
  u8g2.drawBox(0, 2, 64, 30);
  u8g2.setFont(u8g2_font_6x10_mf);
  u8g2.setDrawColor(2);
  u8g2.drawStr(15, 10, "Pytomo");
  u8g2.drawStr(10, 20, "by Tomas");
  u8g2.drawStr(10, 30, "Odstrcil");
  u8g2.drawStr(2, 45, "available");
  u8g2.drawStr(2, 55, "SXR arrays");

  u8g2.drawXBMP( 70, 1, asdex_logo_width, asdex_logo_height, asdex);

  switch(arrayVal){
    case 0: drawArray(F, 38);break;
    case 1: drawArray(G, 38); break;
    case 2: drawArray(H1,20);  break;
    case 3: drawArray(H2,32); break;
    case 4: drawArray(H3,32); break;
    case 5: drawArray(I1,8); break;
    case 6: drawArray(I2,46);break;
    case 7: drawArray(I3,12); break;
    case 8: drawArray(J1,34); break;
    case 9: drawArray(J2,32); break;
    case 10: drawArray(J3,22); break;
    case 11: drawArray(K1,26); break;
    case 12: drawArray(K2,28); break;
    case 13: drawArray(L,36); break;
    case 14: drawArray(M,38); break;
    case 15: drawArray(T,34); break;
  }
  
  u8g2.sendBuffer();// transfer internal memory to the display
  if(arrayVal > 15){
    arrayVal = 0;
  } else{ arrayVal = arrayVal +1; }
  while (digitalRead(7) == HIGH) {
  //  delay(30);
  //digitalWrite(6, HIGH);
  //  delayMicroseconds(100);
  //digitalWrite(6, LOW);
  } 
  //delay(1000);
   
}

void drawArray(const u8g2_uint_t temp[], int len) {
  int i;
  for(i=0;i<len;i=i+2){
    u8g2.drawLine(70 + temp[0],1 + temp[1],70 + temp[i],1 + temp[i+1]);
  }

}

