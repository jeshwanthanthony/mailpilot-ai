package com.mailpilot.intelligence;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(TriageController.class)
@Import(TriageScorer.class)
class TriageControllerTest {
  @Autowired private MockMvc mvc;

  @Test
  void scoresABatch() throws Exception {
    mvc.perform(post("/api/v1/triage/score-batch")
            .contentType(MediaType.APPLICATION_JSON)
            .content("""
                {"messages":[{"id":"m-1","subject":"Action required","sender":"a@example.com",
                "snippet":"Please confirm","unread":true}]}
                """))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.results[0].id").value("m-1"))
        .andExpect(jsonPath("$.results[0].priority").value("high"));
  }

  @Test
  void rejectsAnEmptyBatch() throws Exception {
    mvc.perform(post("/api/v1/triage/score-batch")
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"messages\":[]}"))
        .andExpect(status().isBadRequest());
  }
}
