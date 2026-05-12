package com.example.cube_poc.dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class AlbumResponseDto {
    private String artistName;
    private String albumTitle;
    private String serialNumber;
    private String ownerName;
    private String message;
}
