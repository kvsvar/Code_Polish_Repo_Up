package com.example.studytracker;

public class StudySession {
    private long id;
    private String subject;
    private int minutes;

    public StudySession() {}

    public StudySession(long id, String subject, int minutes) {
        this.id = id;
        this.subject = subject;
        this.minutes = minutes;
    }

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getSubject() { return subject; }
    public void setSubject(String subject) { this.subject = subject; }

    public int getMinutes() { return minutes; }
    public void setMinutes(int minutes) { this.minutes = minutes; }
}
