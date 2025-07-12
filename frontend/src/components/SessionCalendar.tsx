import { useState } from "react";
import { Calendar, Clock, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { SessionDetails } from "./SessionDetails";

interface Session {
  id: string;
  title: string;
  time: string;
  duration: string;
  participants: number;
  activityLogs: ActivityLog[];
}

interface ActivityLog {
  id: string;
  title: string;
  description: string;
  score: number;
}

const mockSessions: Session[] = [
  {
    id: "1",
    title: "Team Sprint Planning",
    time: "09:00",
    duration: "2h",
    participants: 5,
    activityLogs: [
      { id: "1", title: "Backlog Review", description: "Reviewed and prioritized user stories", score: 8 },
      { id: "2", title: "Velocity Planning", description: "Estimated team capacity for next sprint", score: 7 },
      { id: "3", title: "Task Assignment", description: "Assigned tasks to team members", score: 9 },
    ]
  },
  {
    id: "2",
    title: "Client Presentation",
    time: "14:00",
    duration: "1h",
    participants: 3,
    activityLogs: [
      { id: "4", title: "Demo Preparation", description: "Set up demo environment and test scenarios", score: 9 },
      { id: "5", title: "Feature Showcase", description: "Presented new features to client", score: 8 },
      { id: "6", title: "Feedback Collection", description: "Gathered client feedback and next steps", score: 7 },
    ]
  },
  {
    id: "3",
    title: "Code Review Session",
    time: "16:30",
    duration: "1.5h",
    participants: 4,
    activityLogs: [
      { id: "7", title: "Architecture Review", description: "Reviewed system architecture changes", score: 8 },
      { id: "8", title: "Security Audit", description: "Checked for security vulnerabilities", score: 9 },
      { id: "9", title: "Performance Analysis", description: "Analyzed code performance metrics", score: 6 },
    ]
  },
];

const daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const timeSlots = Array.from({ length: 10 }, (_, i) => `${9 + i}:00`);

export function SessionCalendar() {
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);

  const getSessionsForTimeSlot = (day: number, time: string) => {
    // Mock logic - in real app this would filter by actual date/time
    if (day === 0 && time === "9:00") return [mockSessions[0]];
    if (day === 2 && time === "14:00") return [mockSessions[1]];
    if (day === 4 && time === "16:00") return [mockSessions[2]];
    return [];
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="flex items-center justify-center w-12 h-12 bg-gradient-primary rounded-xl shadow-card">
          <Calendar className="w-6 h-6 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-foreground">Session Calendar</h1>
          <p className="text-muted-foreground">Track and manage your team sessions</p>
        </div>
      </div>

      {/* Calendar Grid */}
      <Card className="bg-gradient-card shadow-card border-border">
        <div className="p-6">
          {/* Days Header */}
          <div className="grid grid-cols-8 gap-4 mb-4">
            <div className="text-sm font-medium text-muted-foreground">Time</div>
            {daysOfWeek.map((day) => (
              <div key={day} className="text-sm font-medium text-center text-muted-foreground">
                {day}
              </div>
            ))}
          </div>

          {/* Time Slots */}
          <div className="space-y-2">
            {timeSlots.map((time) => (
              <div key={time} className="grid grid-cols-8 gap-4 min-h-[60px]">
                <div className="flex items-center text-sm text-muted-foreground font-medium">
                  {time}
                </div>
                {Array.from({ length: 7 }, (_, dayIndex) => {
                  const sessions = getSessionsForTimeSlot(dayIndex, time);
                  return (
                    <div key={dayIndex} className="space-y-1">
                      {sessions.map((session) => (
                        <button
                          key={session.id}
                          onClick={() => setSelectedSession(session)}
                          className="w-full p-2 bg-calendar-event hover:bg-calendar-event-hover 
                                   text-primary-foreground rounded-lg shadow-event
                                   transition-all duration-300 hover:scale-105 
                                   hover:shadow-lg text-left text-xs font-medium
                                   border border-primary/20"
                        >
                          <div className="flex items-center gap-1 mb-1">
                            <Clock className="w-3 h-3" />
                            <span>{session.duration}</span>
                          </div>
                          <div className="truncate">{session.title}</div>
                          <div className="flex items-center gap-1 mt-1 opacity-90">
                            <Users className="w-3 h-3" />
                            <span>{session.participants}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Session Details Dialog */}
      <Dialog open={!!selectedSession} onOpenChange={() => setSelectedSession(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden bg-gradient-card shadow-modal">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-foreground">
              {selectedSession?.title}
            </DialogTitle>
          </DialogHeader>
          {selectedSession && (
            <SessionDetails
              session={selectedSession}
              onClose={() => setSelectedSession(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}