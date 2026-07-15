package com.mailpilot.intelligence;

import static com.mailpilot.intelligence.TriageModels.BatchRequest;
import static com.mailpilot.intelligence.TriageModels.BatchResponse;

import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/triage")
class TriageController {
  private final TriageScorer scorer;

  TriageController(TriageScorer scorer) {
    this.scorer = scorer;
  }

  @PostMapping("/score-batch")
  BatchResponse scoreBatch(@Valid @RequestBody BatchRequest request) {
    return new BatchResponse(request.messages().stream().map(scorer::score).toList());
  }
}
