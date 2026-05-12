package com.example.cube_poc.service;

import com.example.cube_poc.dto.AlbumRequestDto;
import com.example.cube_poc.dto.AlbumResponseDto;
import com.example.cube_poc.entity.Album;
import com.example.cube_poc.repository.AlbumRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AlbumService {
    private final AlbumRepository albumRepository;

    public AlbumResponseDto identifyAlbum(AlbumRequestDto requestDto) {
        List<String> texts = requestDto.getExtractedTexts();

        Album album = albumRepository.findByArtistNameAndAlbumTitleIn(texts, texts)
                .orElseThrow(() -> new RuntimeException("앨범 정보를 찾을 수 없습니다."));

            return AlbumResponseDto.builder()
                    .artistName(album.getArtistName())
                    .albumTitle(album.getAlbumTitle())
                    .serialNumber(album.getSerialNumber())
                    .ownerName(album.getOwnerName())
                    .message("앨범 정보 조회 성공")
                    .build();
    }

}
