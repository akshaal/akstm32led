// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "stm32f1xx_hal.h"

#include "ak_rtos.h"
#include "ak_led_fatal_ind.h"

static UART_HandleTypeDef huart1;
static void ak_uart_task(void *argument);

static uint8_t hw[] = "hello world\n";

void ak_uart_init() {
    /* USART1 init function */
    huart1.Instance = USART1;
    huart1.Init.BaudRate = 9600;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;

    if (HAL_UART_Init(&huart1) != HAL_OK) {
        ak_led_fatal_ind_loop(ak_led_fatal_pattern_uart_init);
    }

    HAL_UART_Transmit_IT(&huart1, hw, sizeof(hw)-1);

    // Create uart task
    //ak_task_create("uart", ak_main_task, ak_main_task_priority);
}

__attribute__((noreturn))
static void ak_uart_task(void *argument) {
    for(;;) {
    }
}

void USART1_IRQHandler(void) {
    HAL_UART_IRQHandler(&huart1);
}
