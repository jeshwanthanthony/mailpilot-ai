package com.mailpilot.intelligence;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class TriageScorerTest {
  private final TriageScorer scorer = new TriageScorer();

  @Test
  void marksUrgentActionableMessagesAsUrgent() {
    var result = scorer.score(new TriageModels.TriageRequest(
        "m-1", "Urgent: approval needed", "client@example.com", "Please confirm by the deadline", true));

    assertThat(result.score()).isEqualTo(100);
    assertThat(result.priority()).isEqualTo("urgent");
    assertThat(result.signals()).contains("Urgency language", "Explicit action requested", "Unread message");
  }

  @Test
  void demotesBulkAutomatedMessages() {
    var result = scorer.score(new TriageModels.TriageRequest(
        "m-2", "Weekly digest", "newsletter@example.com", "Updates and unsubscribe", false));

    assertThat(result.score()).isZero();
    assertThat(result.priority()).isEqualTo("low");
    assertThat(result.signals()).containsExactly("Automated sender", "Bulk email pattern");
  }

  @Test
  void keepsOrdinaryUnreadMessagesNormal() {
    var result = scorer.score(new TriageModels.TriageRequest(
        "m-3", "Project notes", "teammate@example.com", "Here are the notes", true));

    assertThat(result.score()).isEqualTo(20);
    assertThat(result.priority()).isEqualTo("normal");
  }
}
