package com.AlgoGym.backend.service;

import com.AlgoGym.backend.model.JudgeLanguage;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Service
public class Judge0LanguageService {

    @Value("${judge0.api.key}")
    private String apiKey;

    @Value("${judge0.api.host}")
    private String apiHost;

    private final RestTemplate restTemplate = new RestTemplate();
    private List<JudgeLanguage> languages = new ArrayList<>();

    @PostConstruct
    public void loadLanguages() {

        String url = "https://judge0-ce.p.rapidapi.com/languages";

        HttpHeaders headers = new HttpHeaders();
        headers.set("X-RapidAPI-Key", apiKey);
        headers.set("X-RapidAPI-Host", apiHost);

        HttpEntity<String> entity = new HttpEntity<>(headers);

        ResponseEntity<JudgeLanguage[]> response =
                restTemplate.exchange(
                        url,
                        HttpMethod.GET,
                        entity,
                        JudgeLanguage[].class
                );

        languages = Arrays.asList(response.getBody());

        System.out.println("Languages Loaded: " + languages.size());
    }

    public List<JudgeLanguage> getLanguages() {
        return languages;
    }
}
