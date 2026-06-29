package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.model.JudgeLanguage;
import com.AlgoGym.backend.service.Judge0LanguageService;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/languages")
@CrossOrigin(origins = "http://localhost:5173")
public class LanguageController {

    private final Judge0LanguageService languageService;

    public LanguageController(Judge0LanguageService languageService) {
        this.languageService = languageService;
    }

    @GetMapping
    public List<JudgeLanguage> getLanguages() {
        return languageService.getLanguages();
    }
}
