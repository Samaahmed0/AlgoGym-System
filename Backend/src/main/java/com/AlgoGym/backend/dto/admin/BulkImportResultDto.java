package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class BulkImportResultDto {
    private int imported;
    private int skipped;
    private int failed;
    private List<String> errors = new ArrayList<>();
}
