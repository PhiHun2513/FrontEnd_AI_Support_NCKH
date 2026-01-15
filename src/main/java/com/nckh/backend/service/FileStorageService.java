package com.nckh.backend.service;

import com.nckh.backend.dto.DocumentResponse;
import com.nckh.backend.entity.Document;
import com.nckh.backend.repository.DocumentRepository;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.io.IOException;
import java.nio.file.*;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class FileStorageService {

    private final DocumentRepository documentRepository;
    private final Path fileStorageLocation = Paths.get("uploads").toAbsolutePath().normalize();

    @PostConstruct
    public void init() {
        try {
            Files.createDirectories(this.fileStorageLocation);
        } catch (Exception ex) {
            throw new RuntimeException("Không thể tạo thư mục lưu trữ file.", ex);
        }
    }

    public DocumentResponse storeFile(MultipartFile file) {
        // Làm sạch tên file để tránh lỗi đường dẫn
        String originalFileName = file.getOriginalFilename();
        if(originalFileName == null) originalFileName = "unknown_file";
        String fileName = System.currentTimeMillis() + "_" + originalFileName;

        try {
            Path targetLocation = this.fileStorageLocation.resolve(fileName);
            Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);

            Document doc = Document.builder()
                    .fileName(originalFileName)
                    .fileType(file.getContentType())
                    .filePath(targetLocation.toString())
                    .fileSize(file.getSize())
                    .build();

            Document savedDoc = documentRepository.save(doc);

            return mapToDTO(savedDoc);

        } catch (IOException ex) {
            throw new RuntimeException("Không thể lưu file " + fileName, ex);
        }
    }

    public List<DocumentResponse> getAllFiles() {
        return documentRepository.findAll().stream()
                .map(this::mapToDTO)
                .collect(Collectors.toList());
    }

    private DocumentResponse mapToDTO(Document doc) {
        String downloadUrl = ServletUriComponentsBuilder.fromCurrentContextPath()
                .path("/api/documents/download/")
                .path(doc.getId().toString())
                .toUriString();

        return DocumentResponse.builder()
                .id(doc.getId())
                .fileName(doc.getFileName())
                .fileType(doc.getFileType())
                .fileSize(doc.getFileSize())
                .uploadTime(doc.getUploadedAt())
                .downloadUrl(downloadUrl)
                .build();
    }
}