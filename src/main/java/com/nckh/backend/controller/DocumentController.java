package com.nckh.backend.controller;

import com.nckh.backend.dto.DocumentResponse;
import com.nckh.backend.service.FileStorageService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.util.List;

@RestController
@RequestMapping("/api/documents")
@RequiredArgsConstructor
@CrossOrigin(origins = "*", allowedHeaders = "*")
public class DocumentController {

    private final FileStorageService fileStorageService;

    @PostMapping("/upload")
    public ResponseEntity<DocumentResponse> uploadFile(@RequestParam("file") MultipartFile file) {
        return ResponseEntity.ok(fileStorageService.storeFile(file));
    }

    @GetMapping
    public ResponseEntity<List<DocumentResponse>> getAllFiles() {
        return ResponseEntity.ok(fileStorageService.getAllFiles());
    }
}