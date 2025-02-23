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

	if !validateMethod(w, r, http.MethodPost) {
		return
	}

	contentType := r.Header.Get("Content-Type")

	switch {
	case strings.HasPrefix(contentType, "multipart/form-data"):
		handleFileUpload(w, r)
	case contentType == "text/plain":
		handleTextContent(w, r)
	default:
		sendErrorResponse(w, http.StatusBadRequest, "Unsupported Content-Type")
	}
}

// Валидация HTTP метода
func validateMethod(w http.ResponseWriter, r *http.Request, allowedMethod string) bool {
	if r.Method == allowedMethod {
		return true
	}
	w.WriteHeader(http.StatusMethodNotAllowed)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "error",
		"message": "Method not allowed",
	})
	return false
}

// Обработка файловых загрузок
func handleFileUpload(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(10 << 20); err != nil {
		log.Printf("Parse multipart error: %v", err)
		sendErrorResponse(w, http.StatusBadRequest, "Failed to parse form data")
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		log.Printf("File retrieval error: %v", err)
		sendErrorResponse(w, http.StatusBadRequest, "No file provided")
		return
	}
	defer file.Close()

	targetPath, err := getUniqueFilePath(header.Filename)
	if err != nil {
		log.Printf("Path error: %v", err)
		sendErrorResponse(w, http.StatusInternalServerError, "File path error")
		return
	}

	if err := saveUploadedFile(file, targetPath); err != nil {
		log.Printf("File save error: %v", err)
		sendErrorResponse(w, http.StatusInternalServerError, "Failed to save file")
		return
	}

	log.Printf("File saved: %s", targetPath)
	sendSuccessResponse(w)
}

// Обработка текстового контента
func handleTextContent(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		log.Printf("Body read error: %v", err)
		sendErrorResponse(w, http.StatusInternalServerError, "Failed to read body")
		return
	}
	defer r.Body.Close()

	if err := copyToClipboard(string(body)); err != nil {
		log.Printf("Clipboard error: %v", err)
		sendErrorResponse(w, http.StatusInternalServerError, "Clipboard operation failed")
		return
	}

	log.Printf("Text copied to clipboard: %s", body)
	sendSuccessResponse(w)
}

// Генерация уникального пути файла
func getUniqueFilePath(originalName string) (string, error) {
	downloadsPath := "D:\\OKBOOMER\\3агрузки"

	baseName := filepath.Base(originalName)
	targetPath := filepath.Join(downloadsPath, baseName)

	if _, err := os.Stat(targetPath); err == nil {
		ext := filepath.Ext(baseName)
		name := strings.TrimSuffix(baseName, ext)
		timestamp := time.Now().Format("2006-01-02-15-04-05")
		return filepath.Join(downloadsPath, fmt.Sprintf("%s_%s%s", name, timestamp, ext)), nil
	}

	return targetPath, nil
}

// Сохранение файла на диск
func saveUploadedFile(src io.Reader, dstPath string) error {
	dstFile, err := os.Create(dstPath)
	if err != nil {
		return err
	}
	defer dstFile.Close()

	if _, err := io.Copy(dstFile, src); err != nil {
		return err
	}
	return nil
}

// Работа с буфером обмена Windows
func copyToClipboard(text string) error {
	cmd := exec.Command("cmd", "/c", "clip")
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return err
	}

	go func() {
		defer stdin.Close()
		io.WriteString(stdin, text)
	}()

	return cmd.Run()
}

// Утилиты для отправки ответов
func sendErrorResponse(w http.ResponseWriter, statusCode int, message string) {
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "error",
		"message": message,
	})
}

func sendSuccessResponse(w http.ResponseWriter) {
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
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

	flag.StringVar(&host, "host", "", "Server host (default: HOST env var or 192.168.1.64)")
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
		host = "192.168.1.64"
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
