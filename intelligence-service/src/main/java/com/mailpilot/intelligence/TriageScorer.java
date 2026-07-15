package com.mailpilot.intelligence;

import static com.mailpilot.intelligence.TriageModels.TriageRequest;
import static com.mailpilot.intelligence.TriageModels.TriageResult;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Service;

@Service
class TriageScorer {
  TriageResult score(TriageRequest message) {
    var searchable = (message.subject() + " " + message.snippet()).toLowerCase(Locale.ROOT);
    var sender = message.sender().toLowerCase(Locale.ROOT);
    var score = 10;
    var signals = new ArrayList<String>();

    score += signal(searchable, List.of("urgent", "asap", "blocking", "time-sensitive"), 35,
        "Urgency language", signals);
    score += signal(searchable, List.of("deadline", "due today", "due tomorrow", "overdue"), 25,
        "Deadline detected", signals);
    score += signal(searchable, List.of("action required", "approval needed", "please confirm", "respond by"),
        20, "Explicit action requested", signals);
    score += signal(searchable, List.of("security", "invoice", "payment", "contract"), 15,
        "Sensitive business topic", signals);

    if (message.unread()) {
      score += 10;
      signals.add("Unread message");
    }
    if (sender.contains("no-reply") || sender.contains("noreply") || sender.contains("newsletter")) {
      score -= 25;
      signals.add("Automated sender");
    }
    if (searchable.contains("unsubscribe")) {
      score -= 20;
      signals.add("Bulk email pattern");
    }

    var boundedScore = Math.clamp(score, 0, 100);
    return new TriageResult(message.id(), boundedScore, priority(boundedScore), List.copyOf(signals));
  }

  private int signal(
      String text, List<String> terms, int weight, String label, List<String> signals) {
    if (terms.stream().anyMatch(text::contains)) {
      signals.add(label);
      return weight;
    }
    return 0;
  }

  private String priority(int score) {
    if (score >= 70) return "urgent";
    if (score >= 40) return "high";
    if (score >= 15) return "normal";
    return "low";
  }
}
