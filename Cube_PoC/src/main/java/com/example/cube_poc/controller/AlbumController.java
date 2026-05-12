package com.example.cube_poc.controller;

import com.example.cube_poc.dto.AlbumRequestDto;
import com.example.cube_poc.dto.AlbumResponseDto;
import com.example.cube_poc.service.AlbumService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/album")
@RequiredArgsConstructor
public class AlbumController {
    private final AlbumService albumService;

    @PostMapping("/info")
    public ResponseEntity<AlbumResponseDto> getAlbuminfo(@RequestBody AlbumRequestDto requestDto) {
        AlbumResponseDto response = albumService.identifyAlbum(requestDto);
        return ResponseEntity.ok(response);
    }
}
