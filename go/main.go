package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"time"
)

const (
	expectedToken = "my_secret_token"
	resultURL        = "http://localhost:8000/api/async_result/"
)

type TestResult struct {
	IdTest       int    `json:"id_test"`
	TestStatus int    `json:"test_status"`
	Token         string `json:"token"`
}

type RequestBody struct {
	IdTest int    `json:"id_test"`
	Token   string `json:"token"`
}

// Функция для преобразования числа в соответствующее слово
func getStatusWord(status int) string {


	// ('f', 'Завершён'), # завершён - 'finished'= успех
	// ('c', 'Отменён'), # отменён - 'cancelled' = неуспех

	switch status {
	case 1:
		return "успех"
	case 2:
		return "Неуспех"
	default:
		return "Неизвестный статус"
	}
}

func main() {
	http.HandleFunc("/api/async_calc/", handleProcess)
	fmt.Println("Server running at port :8100")
	http.ListenAndServe(":8100", nil)
}

func handleProcess(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "The method is not allowed", http.StatusMethodNotAllowed)
		return
	}

	var requestBody RequestBody
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(&requestBody); err != nil {
		http.Error(w, "Error decoding JSON", http.StatusBadRequest)
		fmt.Println("Error decoding JSON:", err)
		return
	}

	id_test := requestBody.IdTest
	token := requestBody.Token
	fmt.Println(id_test, token)

	if token == "" || token != expectedToken {
		http.Error(w, "Токены не совпадают", http.StatusForbidden)
		fmt.Println("Токены не совпадают")
		fmt.Println(token, expectedToken)
		return
	}

	// Генерируем случайное число в диапазоне [0.0, 1.0)
	randomValue := rand.Float64()

	var test_status int
	// 70% шанс для Успеха
	if randomValue < 0.7 {
		test_status = 1
		// 30% шанс для Неуспеха
	} else {
		test_status = 2
	}

	// Успешный ответ в формате JSON
	successMessage := map[string]interface{}{
		"message":        "Successful",
		"test_status": getStatusWord(test_status),
		"data": TestResult{
			IdTest:       id_test,
			TestStatus:   test_status,
			Token:        token,
		},
	}

	jsonResponse, err := json.Marshal(successMessage)
	if err != nil {
		http.Error(w, "Error encoding JSON", http.StatusInternalServerError)
		fmt.Println("Ошибка кодирования JSON:", err)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(jsonResponse)

	go func() {
		// Задержка 5 секунд
		delay := 5
		time.Sleep(time.Duration(delay) * time.Second)

		// Отправка результата на другой сервер
		result := TestResult{
			IdTest:       id_test,
			TestStatus:   test_status,
			Token:        token,
		}

		fmt.Println("json", result)
		jsonValue, err := json.Marshal(result)
		if err != nil {
			fmt.Println("Ошибка при маршализации JSON:", err)
			return
		}

		req, err := http.NewRequest(http.MethodPut, resultURL, bytes.NewBuffer(jsonValue))
		if err != nil {
			fmt.Println("Ошибка при создании запроса на обновление:", err)
			return
		}
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		

		randomValue_g := rand.Float64()

		// var do_send int
		// // 70% шанс для Успеха
		// if randomValue_g>5 {
		// 	resp, err := client.Do(req)
		// 	if err != nil {
		// 		fmt.Println("Ошибка при отправке запроса на обновление:", err)
		// 		return
		// 	}
		// }
		// defer resp.Body.Close()

		fmt.Println("Ответ от сервера обновления:", resp.Status)
	}()
}