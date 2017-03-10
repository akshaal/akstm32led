// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "stm32f1xx_hal.h"

#include "FreeRTOS.h"
#include "portable.h"
#include "task.h"
#include "string.h"

#include "ak_rtos.h"
#include "ak_uart.h"
#include "ak_led_fatal_ind.h"

static UART_HandleTypeDef huart1;
static ak_task_handle tx_task_handle;
static ak_queue_handle tx_task_queue;

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

    // Create TX queue
    tx_task_queue = ak_queue_create(AK_UART_TX_QUEUE_SIZE, sizeof(char*));

    // Create uart task
    tx_task_handle = ak_task_create("uart_tx", ak_uart_tx_task, ak_uart_tx_task_priority);
}

void ak_uart_send(char *str) {
    char *dupped = ak_malloc(strlen(str));
    strcpy(dupped, str);
    xQueueSendToBack(tx_task_queue, &dupped, 0);
}

__attribute__((noreturn))
static void ak_uart_tx_task(void *argument) {
    ak_uart_send("Welcome!\r\n");

    for(;;) {
        char *str;

        // Wait for a sting to be queued. Returns false if timeout... (nothing to send)
        int queue_rc = xQueueReceive(tx_task_queue, &str, AK_TICK_IN_DAY);
        if (queue_rc == pdFALSE) {
            continue; // Try again
        }

        // Begin non-blocking interrupt-based transmission
        HAL_UART_Transmit_IT(&huart1, (uint8_t*)str, strlen(str));

        // Block this FreeRTOS thread until we get notification from HAL_UART_TxCpltCallback (called from ISR)
        // this can also timeout...
        ulTaskNotifyTake( /* xClearCountOnExit = */ pdTRUE, pdMS_TO_TICKS(1000));

        // Free memory
        ak_free(str);
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
