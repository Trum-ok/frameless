package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// index (/)
func indexHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"msg": "Hi!!"})
}

// health
func healthHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// drop
func dropHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// Проверка метода
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		json.NewEncoder(w).Encode(map[string]string{"status": "error", "message": "Method not allowed"})
		return
	}

	contentType := r.Header.Get("Content-Type")

	// Обработка multipart/form-data (файлы)
	if strings.HasPrefix(contentType, "multipart/form-data") {
		// Парсим форму с ограничением размера 10 MB
		err := r.ParseMultipartForm(10 << 20)
		if err != nil {
			log.Printf("Failed to parse multipart form: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Failed to parse form data",
			})
			return
		}

		// Извлекаем файл из запроса
		file, header, err := r.FormFile("file")
		if err != nil {
			log.Printf("Failed to get file: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "No file provided",
			})
			return
		}
		defer file.Close()

		// Получаем путь к папке Downloads
		homeDir, err := os.UserHomeDir()
		if err != nil {
			log.Printf("Failed to get home directory: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Failed to locate downloads directory",
			})
			return
		}
		downloadsPath := filepath.Join(homeDir, "Downloads")

		// Создаем папку если нужно
		if err := os.MkdirAll(downloadsPath, 0755); err != nil {
			log.Printf("Failed to create downloads directory: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Failed to create downloads directory",
			})
			return
		}

		// Создаем целевой файл
		filename := filepath.Base(header.Filename)
		targetPath := filepath.Join(downloadsPath, filename)
		outFile, err := os.Create(targetPath)
		if err != nil {
			log.Printf("Failed to create file: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Failed to save file",
			})
			return
		}
		defer outFile.Close()

		// Копируем содержимое
		if _, err := io.Copy(outFile, file); err != nil {
			log.Printf("Failed to save file content: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Failed to write file content",
			})
			return
		}

		log.Printf("File saved: %s", targetPath)
		json.NewEncoder(w).Encode(map[string]string{"status": "success"})
		return
	}

	// Обработка text/plain (текст)
	if contentType == "text/plain" {
		body, err := io.ReadAll(r.Body)
		if err != nil {
			log.Printf("Failed to read body: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Failed to read body",
			})
			return
		}
		defer r.Body.Close()

		// Копирование в буфер обмена (оригинальная логика)
		cmd := exec.Command("pbcopy")
		stdinPipe, err := cmd.StdinPipe()
		if err != nil {
			log.Printf("Failed to get stdin pipe: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Clipboard access failed",
			})
			return
		}

		go func() {
			defer stdinPipe.Close()
			if _, err := io.WriteString(stdinPipe, string(body)); err != nil {
				log.Printf("Failed to write to clipboard: %v", err)
			}
		}()

		if err := cmd.Run(); err != nil {
			log.Printf("Clipboard error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "error",
				"message": "Clipboard operation failed",
			})
			return
		}

		log.Printf("Received text: %s", body)
		json.NewEncoder(w).Encode(map[string]string{"status": "success"})
		return
	}

	// Неподдерживаемый Content-Type
	w.WriteHeader(http.StatusBadRequest)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "error",
		"message": "Unsupported Content-Type",
	})
}

// Логирование
func loggingMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log.Printf("%s %s %s", r.RemoteAddr, r.Method, r.URL)
		next(w, r)
	}
}

func main() {
	var host, port string

	flag.StringVar(&host, "host", "", "Server host (default: HOST env var or 192.168.1.73)")
	flag.StringVar(&port, "port", "", "Server port (default: S_PORT env var or 1161)")
	flag.Parse()

	// Настройка маршрутов
	http.HandleFunc("/", loggingMiddleware(indexHandler))
	http.HandleFunc("/health", loggingMiddleware(healthHandler))
	http.HandleFunc("/drop", loggingMiddleware(dropHandler))

	// .env
	if host == "" {
		host = os.Getenv("HOST")
	}
	if host == "" {
		host = "192.168.1.73"
	}

	if port == "" {
		port = os.Getenv("S_PORT")
	}
	if port == "" {
		port = "1161"
	}
	addr := fmt.Sprintf("%s:%s", host, port)

	// Запуск сервера
	log.Printf("Starting server on %s", addr)
	server := &http.Server{
		Addr:         addr,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  30 * time.Second,
	}

	if err := server.ListenAndServe(); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
