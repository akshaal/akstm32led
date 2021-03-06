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

static char const seq_up[] = {0x1B, 0x5B, 0x41};
static char const seq_down[] = {0x1B, 0x5B, 0x42};
static char const seq_left[] = {0x1B, 0x5B, 0x44};
static char const seq_right[] = {0x1B, 0x5B, 0x43};

// ==================================================
// Local function definitions

static void ak_uart_tx_task();
static void ak_uart_rx_task();

// ==================================================
// Implementation

void ak_uart_init() {
    /* USART1 init function */
    huart1.Instance = USART1;
    huart1.Init.BaudRate = 115200;
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

void ak_uart_send(char const * const str) {
    char const * const dupped = ak_strdup(str);
    if (xQueueSendToBack(tx_queue, &dupped, 0) == errQUEUE_FULL) {
        ak_free(dupped);
    }
}

void queue_rx(char const * const str, size_t const len) {
    char const * const dupped = ak_strndup(str, len);
    if (xQueueSendToBack(rx_queue, &dupped, 0) == errQUEUE_FULL) {
        ak_free(dupped);
    }
}

char *ak_uart_receive() {
    char * str;
    for (;;) {
        int const queue_rc = xQueueReceive(rx_queue, &str, AK_TICKS_IN_DAY);
        if (queue_rc == pdFALSE) {
            continue; // Try again
        }
        return str;
    }
}

__attribute__((noreturn))
static void ak_uart_tx_task() {
    for(;;) {
        char *str;

        // Wait for a sting to be queued. Returns false if timeout... (nothing to send)
        int const queue_rc = xQueueReceive(tx_queue, &str, AK_TICKS_IN_DAY);
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
static void ak_uart_rx_task() {
    static char rx_buf[AK_UART_RX_BUF_LEN];
    static int rx_buf_count;

    // Enable interrupt RX Not Empty Interrupt
    __HAL_UART_ENABLE_IT(&huart1, UART_IT_RXNE);

    rx_buf_count = 0;

    for(;;) {
        // If there is something received, then we clear it in 60 seconds anyway, otherwise no need to wake up
        int const timeout = rx_buf_count ? pdMS_TO_TICKS(60000) : AK_TICKS_IN_DAY;

        // Wait for a char to be queued. Returns false if timeout... (nothing received)
        char * const buf_empty_pos = rx_buf + rx_buf_count;

        int const queue_rc = xQueueReceive(rx_char_queue, buf_empty_pos, timeout);
        if (queue_rc == pdFALSE) {
            rx_buf_count = 0;
            continue; // Try again
        }

        // Process
        char const c = *buf_empty_pos;

        if (c == '\r') {
            if (rx_buf_count) {
                // There is some cmd in buffer
                // ECHO newline
                ak_uart_send("!!!\r\n");

                // Queue newline into rx_queue
                queue_rx(rx_buf, rx_buf_count);

                // Reset our buffer position
                rx_buf_count = 0;
            } else {
                // No data in buffer, just echo..
                // ECHO newline
                ak_uart_send("\r\n");
            }
        } else if (rx_buf_count < AK_UART_RX_BUF_LEN - 1) {
            // Not overflow
            rx_buf_count++;

            // ECHO
            if (*rx_buf == 0x1b) {
                // Seems like an escape sequence
                if (rx_buf_count == sizeof(seq_up) && !strncmp(rx_buf, seq_up, sizeof(seq_up))) {
                    queue_rx(AK_UART_UP_KEY, sizeof(AK_UART_UP_KEY));
                    rx_buf_count = 0;
                } else if (rx_buf_count == sizeof(seq_down) && !strncmp(rx_buf, seq_down, sizeof(seq_down))) {
                    queue_rx(AK_UART_DOWN_KEY, sizeof(AK_UART_DOWN_KEY));
                    rx_buf_count = 0;
                } else if (rx_buf_count == sizeof(seq_left) && !strncmp(rx_buf, seq_left, sizeof(seq_left))) {
                    queue_rx(AK_UART_LEFT_KEY, sizeof(AK_UART_LEFT_KEY));
                    rx_buf_count = 0;
                } else if (rx_buf_count == sizeof(seq_right) && !strncmp(rx_buf, seq_right, sizeof(seq_right))) {
                    queue_rx(AK_UART_RIGHT_KEY, sizeof(AK_UART_RIGHT_KEY));
                    rx_buf_count = 0;
                }
            } else {
                // It's not an escape sequence, just echo it...
                char echo_buf[2];
                echo_buf[0] = c;
                echo_buf[1] = '\0';
                ak_uart_send(echo_buf);
            }
        }
    }
}

void USART1_IRQHandler(void) {
    // We handle RX here, but TX is handled by HAL_UART implementation...

    int32_t const flag = __HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE);
    int32_t const it_source = __HAL_UART_GET_IT_SOURCE(&huart1, UART_IT_RXNE);

    if ((flag != RESET) && (it_source != RESET)) {
        // RX. Read data from data register
        char const c = (char)(huart1.Instance->DR & (uint8_t)0x00FF);

        long xHigherPriorityTaskWoken = pdFALSE;
        xQueueSendToBackFromISR(rx_char_queue, &c, &xHigherPriorityTaskWoken);
        portEND_SWITCHING_ISR(xHigherPriorityTaskWoken);
    } else {
        // TX
        HAL_UART_IRQHandler(&huart1);
    }
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef * const huart) {
    if (&huart1 == huart) {
        long xHigherPriorityTaskWoken = pdFALSE;

        // Wake task that's waiting for transmission to be completed
        vTaskNotifyGiveFromISR(tx_task_handle, &xHigherPriorityTaskWoken);

        portEND_SWITCHING_ISR(xHigherPriorityTaskWoken);
    }
}
