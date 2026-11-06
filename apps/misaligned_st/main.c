// Copyright 2021 ETH Zurich and University of Bologna.
// Solderpad Hardware License, Version 0.51, see LICENSE for details.
// SPDX-License-Identifier: SHL-0.51
//
// Author: Luca Caballero Cusin <lcaballero@ethz.ch>

#include "../common/macros/vector/vector_macros.h"
#include "../common/macros/vector/long_array.h"
#include <stdio.h>

static volatile uint16_t buf[256] __attribute__((aligned(32)));
static volatile uint16_t buf2[64] __attribute__((aligned(128)));
static volatile uint16_t buf3[256] __attribute__((aligned(32)));

void TEST_MISALIGNED_STORE(void) {
  

  // Test 1: 1-byte offset (not 2-byte aligned for e16)
  VSET(16, e16, m1);
  VLOAD_16(v1, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8);
  VLOAD_16(v2, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8);
  asm volatile("vse16.v v1, (%0)" ::"r"(&buf3[1]));
  __asm__ volatile("fence");
  for (int i = 0; i < 16; i++) {
    //uint16_t got = (uint16_t)buf[1 + 2*i] | ((uint16_t)buf[2 + 2*i] << 8);
     //if (buf[i]= (uint16_t)(i+1))
    printf("e16+1 FAIL at %d: got %04x expected %04x\n", i, buf3[i+1], i+1);
  }

    asm volatile("vle16.v v2, (%0)" ::"r"(&buf3[1]));
  __asm__ volatile("fence");
  VCMP_U16(10,v2, 1, 2, 3, 4, 5, 6, 7, 8 ,1, 2, 3, 4, 5, 6, 7, 8);

}

void TEST_MISALIGNED_STORE_2(void) {
  

  // Test 1: 1-byte offset (not 2-byte aligned for e16)
  VSET(17, e16, m1);
  VLOAD_16(v1, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8, 1);
  asm volatile("vse16.v v1, (%0)" ::"r"(&buf[0]));
  __asm__ volatile("fence");
  for (int i = 0; i < 17; i++) {
    //uint16_t got = (uint16_t)buf[1 + 2*i] | ((uint16_t)buf[2 + 2*i] << 8);
     //if (buf[i]= (uint16_t)(i+1))
    printf("e16+1 FAIL at %d: got %04x expected %04x\n", i, buf[0], i+1);
  }

    asm volatile("vle16.v v2, (%0)" ::"r"(&buf[0]));
  __asm__ volatile("fence");
  VCMP_U16(10,v2, 1, 2, 3, 4, 5, 6, 7, 8 ,1, 2, 3, 4, 5, 6, 7, 8, 1);

}

void TEST_MISALIGNED_STORE_3(void) {
  

  // Test 1: 1-byte offset (not 2-byte aligned for e16)
  VSET(32, e16, m1);
  VLOAD_16(v1, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8 , 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8);
  VLOAD_16(v2, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8 ,8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8);
  asm volatile("vse16.v v1, (%0)" ::"r"(&buf2[1]));
  __asm__ volatile("fence");
  // for (int i = 0; i < 8; i++) {
  //   //uint16_t got = (uint16_t)buf[1 + 2*i] | ((uint16_t)buf[2 + 2*i] << 8);
  //    //if (buf[i]= (uint16_t)(i+1))
  //   printf("e16+1 FAIL at %d: got %04x expected %04x\n", i, buf_2[0], i+1);
  // }

  asm volatile("vle16.v v1, (%0)" ::"r"(&buf2[0]));
  //__asm__ volatile("fence");
  VCMP_U16(10,v1, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8 , 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8);

}

void TEST_MISALIGNED_STORE_4(void) {
  // 16 x e16 = 32 bytes, stored at every legal 2-byte offset 0..30
  for (int off = 0; off < 32; off += 2) {
    // poison the buffer
    for (int i = 0; i < 128; i++) buf[i] = 0xAAAA;
    asm volatile("fence");

    VSET(16, e16, m1);
    VLOAD_16(v1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16);
    asm volatile("vse16.v v1, (%0)" ::"r"((uint8_t *)&buf[32] + off));
    asm volatile("fence");

    // check: 16 elements land at the offset, the guards before and after are untouched
    for (int i = 0; i < 128; i++) {
      int k = i - 32 - off / 2;                       // element index (uint16_t units)
      uint16_t exp = (k >= 0 && k < 16) ? (uint16_t)(k + 1) : 0xAAAA;
      if (buf[i] != exp)
        printf("FAIL off=%d buf[%d]=%04x exp %04x\n", off, i, buf[i], exp);
    }
  }
}

void TEST_MISALIGNED_STORE_5(void) {
  // e16, off=2, vl=15 (30 bytes) -> ends exactly on the beat boundary, no flush
  for (int i = 0; i < 128; i++) buf[i] = 0xAAAA;
  asm volatile("fence");

  VSET(15, e16, m1);
  VLOAD_16(v1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16);
  asm volatile("vse16.v v1, (%0)" ::"r"((uint8_t *)&buf[32] + 2));
  asm volatile("fence");

  // expected: buf[33..47] = 1..15, everything else untouched
  for (int i = 0; i < 128; i++) {
    int k = i - 33;
    uint16_t exp = (k >= 0 && k < 15) ? (uint16_t)(k + 1) : 0xAAAA;
    if (buf[i] != exp)
      printf("FAIL case1 buf[%d]=%04x exp %04x\n", i, buf[i], exp);
  }
}

void TEST_VSUXEI(void) {
  // 16 x e16 elements scattered to byte offsets idx[i] from a 32-byte-aligned base
  uint16_t *base = &buf[32];

  for (int i = 0; i < 128; i++) buf[i] = 0xAAAA;
  asm volatile("fence");

  VSET(16, e16, m1);
  VLOAD_16(v1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16);   // data
  // byte offsets: element i goes to base + 6*i bytes (3 uint16_t slots apart)
  VLOAD_16(v2, 0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90);   // indices
  asm volatile("vsuxei16.v v1, (%0), v2" ::"r"(base));
  asm volatile("fence");

  // check: element k at buf[32 + 3*k], everything else untouched
  for (int i = 0; i < 128; i++) {
    int rel = i - 32;
    uint16_t exp = 0xAAAA;
    if (rel >= 0 && rel % 3 == 0 && rel / 3 < 16) exp = (uint16_t)(rel / 3 + 1);
    if (buf[i] != exp)
      printf("FAIL vsuxei buf[%d]=%04x exp %04x\n", i, buf[i], exp);
  }
}

void TEST_MISALIGNED_LMUL(void) {
  // e16, m4: up to 4*16 = 64 elements = 128 bytes = 4 beats. Offset 2, vl = 64 -> 5 beats (flush).
  // Then vl = 63 -> 4 beats, no flush. Then vl = 33 -> partial last beat.
  int vls[3] = {64, 63, 33};

  for (int t = 0; t < 3; t++) {
    int vl = vls[t];
    for (int i = 0; i < 256; i++) buf[i] = 0xAAAA;
    asm volatile("fence");

    VSET(64, e16, m4);
    // fill v4..v7 (m4 group) with 1..64
    for (int i = 0; i < 64; i++) buf2[i] = i + 1;       // buf2: separate uint16_t[64] source
    asm volatile("vle16.v v4, (%0)" ::"r"(buf2));
    asm volatile("fence");

    VSET(vl, e16, m4);
    asm volatile("vse16.v v4, (%0)" ::"r"((uint8_t *)&buf[64] + 2));
    asm volatile("fence");

    for (int i = 0; i < 256; i++) {
      int k = i - 65;                                    // element index; buf[65] = base + 2 bytes
      uint16_t exp = (k >= 0 && k < vl) ? (uint16_t)(k + 1) : 0xAAAA;
      if (buf[i] != exp)
        printf("FAIL m4 vl=%d buf[%d]=%04x exp %04x\n", vl, i, buf[i], exp);
    }
  }
}

static volatile uint16_t pbuf[4096] __attribute__((aligned(4096)));   // 8 KiB, page boundary at pbuf[2048]

void TEST_MISALIGNED_PAGE_CROSS(void) {
  // distance in bytes from the store start to the 4 KiB boundary
  int ks[5] = {62, 34, 30, 4, 2};

  for (int i = 0; i < 64; i++) buf2[i] = i + 1;

  for (int t = 0; t < 5; t++) {
    int k = ks[t];
    int start = 2048 - k / 2;                      // pbuf index where the store begins

    for (int i = 1900; i < 2300; i++) pbuf[i] = 0xAAAA;
    asm volatile("fence");

    VSET(64, e16, m4);
    asm volatile("vle16.v v4, (%0)" ::"r"(buf2) : "memory");
    asm volatile("vse16.v v4, (%0)" ::"r"((uint8_t *)&pbuf[2048] - k) : "memory");
    asm volatile("fence");

    for (int i = 1900; i < 2300; i++) {
      int e = i - start;                            // element index
      uint16_t exp = (e >= 0 && e < 64) ? (uint16_t)(e + 1) : 0xAAAA;
      if (pbuf[i] != exp)
        printf("FAIL cross k=%d pbuf[%d]=%04x exp %04x\n", k, i, pbuf[i], exp);
    }
  }
}


int main(void) {
  INIT_CHECK();
  enable_vec();

  // TEST_MISALIGNED_STORE();
  // TEST_MISALIGNED_STORE_2();
  // TEST_MISALIGNED_STORE_3();
  TEST_MISALIGNED_STORE_4();
  TEST_MISALIGNED_STORE_5();
  TEST_VSUXEI();
  TEST_MISALIGNED_LMUL();
  TEST_MISALIGNED_PAGE_CROSS();
  

  EXIT_CHECK();
}