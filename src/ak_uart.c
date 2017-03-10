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
static ak_task_handle rx_task_handle;
static ak_queue_handle tx_queue;
static ak_queue_handle rx_queue;
static ak_queue_handle rx_char_queue;
static char rx_buf[AK_UART_RX_BUF_LEN];
static int rx_buf_count;

// ==================================================
// Local function definitions

static void ak_uart_tx_task(void *argument);
static void ak_uart_rx_task(void *argument);

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

    // Create queues
    tx_queue = ak_queue_create(AK_UART_TX_QUEUE_SIZE, sizeof(char*));
    rx_queue = ak_queue_create(AK_UART_RX_QUEUE_SIZE, sizeof(char*));
    rx_char_queue = ak_queue_create(AK_UART_RX_CHAR_QUEUE_SIZE, 1);

    // Create uart task
    tx_task_handle = ak_task_create("uart_tx", ak_uart_tx_task, ak_uart_tx_task_priority);
    rx_task_handle = ak_task_create("uart_rx", ak_uart_rx_task, ak_uart_rx_task_priority);
}

void ak_uart_send(char *str) {
    char *dupped = ak_malloc(strlen(str));
    strcpy(dupped, str);
    xQueueSendToBack(tx_queue, &dupped, 0);
}

__attribute__((noreturn))
static void ak_uart_tx_task(void *argument) {
    for(;;) {
        char *str;

        // Wait for a sting to be queued. Returns false if timeout... (nothing to send)
        int queue_rc = xQueueReceive(tx_queue, &str, AK_TICK_IN_DAY);
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

__attribute__((noreturn))
static void ak_uart_rx_task(void *argument) {
    rx_buf_count = 0;

    for(;;) {
        // If there is something received, then we clear it in 60 seconds anyway, otherwise no need to wake up
        int timeout = rx_buf_count ? pdMS_TO_TICKS(60000) : AK_TICK_IN_DAY;

        // Wait for a char to be queued. Returns false if timeout... (nothing received)
        int queue_rc = xQueueReceive(rx_char_queue, rx_buf + rx_buf_count, timeout);
        if (queue_rc == pdFALSE) {
            rx_buf_count = 0;
            continue; // Try again
        }
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
