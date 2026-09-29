package com.example.studytracker;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/sessions")
public class StudySessionController {

    private final List<StudySession> sessions = new ArrayList<>();
    private long nextId = 1;

    @PostMapping
    public StudySession add(@RequestBody StudySession session) {
        session.setId(nextId++);
        sessions.add(session);
        return session;
    }

    @GetMapping
    public List<StudySession> getAll() {
        return sessions;
    }

    @DeleteMapping("/{id}")
    public String delete(@PathVariable long id) {
        boolean removed = sessions.removeIf(s -> s.getId() == id);
        return removed ? "Session deleted" : "Session not found";
    }
}
