// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "stm32f1xx_hal.h"

#include "ak_rtos.h"
#include "ak_led_fatal_ind.h"
#include "portable.h"
#include "task.h"

static UART_HandleTypeDef huart1;
static ak_task_handle tx_task_handle;

// ==================================================
// Local function definitions
static void ak_uart_tx_task(void *argument);

// ==================================================
// Implementation

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

    // Create uart task
    tx_task_handle = ak_task_create("uart_tx", ak_uart_tx_task, ak_uart_tx_task_priority);
}

__attribute__((noreturn))
static void ak_uart_tx_task(void *argument) {
    for(;;) {
        // Begin non-blocking interrupt-based transmission
        HAL_UART_Transmit_IT(&huart1, "hello\r\n", 7);

        // Block this FreeRTOS thread until we get notification from HAL_UART_TxCpltCallback (called from ISR)
        // this can also timeout...
        ulTaskNotifyTake( /* xClearCountOnExit = */ pdTRUE, pdMS_TO_TICKS(1000) );
    }
}

void USART1_IRQHandler(void) {
    HAL_UART_IRQHandler(&huart1);
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart) {
    if (&huart1 == huart) {
        long xHigherPriorityTaskWoken = pdFALSE;

        // Wake task that's waiting for transmission to be completed
        vTaskNotifyGiveFromISR(tx_task_handle, &xHigherPriorityTaskWoken);

        portEND_SWITCHING_ISR( xHigherPriorityTaskWoken );
    }
}
