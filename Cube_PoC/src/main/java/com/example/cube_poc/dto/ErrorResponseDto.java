package com.example.cube_poc.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ErrorResponseDto {
    private int errorCode;
    private String errorMessage;
}
