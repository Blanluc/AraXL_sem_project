// Copyright 2021 ETH Zurich and University of Bologna.
// Solderpad Hardware License, Version 0.51, see LICENSE for details.
// SPDX-License-Identifier: SHL-0.51
//
// Author: Luca Caballero Cusin <lcaballero@ethz.ch>

#include "../common/macros/vector/vector_macros.h"
#include "../common/macros/vector/long_array.h"
#include <stdio.h>

static volatile uint16_t buf[16] __attribute__((aligned(128)));

void TEST_MISALIGNED_STORE(void) {
  

  // Test 1: 1-byte offset (not 2-byte aligned for e16)
  VSET(16, e16, m1);
  VLOAD_16(v1, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8);
  asm volatile("vse16.v v1, (%0)" ::"r"(&buf[1]));
  __asm__ volatile("fence");
  for (int i = 0; i < 16; i++) {
    //uint16_t got = (uint16_t)buf[1 + 2*i] | ((uint16_t)buf[2 + 2*i] << 8);
     //if (buf[i]= (uint16_t)(i+1))
    printf("e16+1 FAIL at %d: got %04x expected %04x\n", i, buf[0], i+1);
  }

    asm volatile("vle16.v v2, (%0)" ::"r"(&buf[0]));
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



int main(void) {
  INIT_CHECK();
  enable_vec();

  TEST_MISALIGNED_STORE();
  //TEST_MISALIGNED_STORE_2();

  EXIT_CHECK();
}