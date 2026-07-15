package com.mailpilot.intelligence;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

final class TriageModels {
  private TriageModels() {}

  record TriageRequest(
      @NotBlank String id,
      @NotNull @Size(max = 500) String subject,
      @NotNull @Size(max = 500) String sender,
      @NotNull @Size(max = 2000) String snippet,
      boolean unread) {}

  record BatchRequest(@NotEmpty @Size(max = 50) List<@Valid TriageRequest> messages) {}

  record TriageResult(
      String id, int score, String priority, List<String> signals) {}

  record BatchResponse(List<TriageResult> results) {}
}
