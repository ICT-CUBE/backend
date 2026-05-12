package com.example.cube_poc.dto;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
public class AlbumRequestDto {
    private List<String> extractedTexts;
}
