import { useState } from "react";
import { Clock, Users, Calendar as CalendarIcon, Star } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface ActivityLog {
  id: string;
  title: string;
  description: string;
  score: number;
}

interface Session {
  id: string;
  title: string;
  time: string;
  duration: string;
  participants: number;
  activityLogs: ActivityLog[];
}

interface SessionDetailsProps {
  session: Session;
  onClose: () => void;
}

export function SessionDetails({ session, onClose }: SessionDetailsProps) {
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>(session.activityLogs);

  const updateScore = (logId: string, newScore: number) => {
    if (newScore >= 0 && newScore <= 10) {
      setActivityLogs(prev => 
        prev.map(log => 
          log.id === logId ? { ...log, score: newScore } : log
        )
      );
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-green-600";
    if (score >= 6) return "text-yellow-600";
    return "text-red-500";
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 8) return "bg-green-50 border-green-200";
    if (score >= 6) return "bg-yellow-50 border-yellow-200";
    return "bg-red-50 border-red-200";
  };

  return (
    <div className="space-y-6 overflow-y-auto max-h-[60vh] pr-2">
      {/* Session Info */}
      <div className="bg-accent/50 rounded-lg p-4 border border-accent">
        <div className="grid grid-cols-3 gap-4">
          <div className="flex items-center gap-2">
            <CalendarIcon className="w-4 h-4 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Time</p>
              <p className="font-medium">{session.time}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Duration</p>
              <p className="font-medium">{session.duration}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Participants</p>
              <p className="font-medium">{session.participants}</p>
            </div>
          </div>
        </div>
      </div>

      <Separator />

      {/* Activity Logs Header */}
      <div className="flex items-center gap-2">
        <Star className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-semibold text-foreground">Activity Logs</h3>
        <span className="text-sm text-muted-foreground">({activityLogs.length} activities)</span>
      </div>

      {/* Activity Logs List */}
      <div className="space-y-3">
        {activityLogs.map((log) => (
          <Card key={log.id} className={`p-4 border transition-all duration-300 hover:shadow-md ${getScoreBgColor(log.score)}`}>
            <div className="flex items-start justify-between gap-4">
              {/* Activity Content */}
              <div className="flex-1 space-y-2">
                <h4 className="font-semibold text-foreground">{log.title}</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {log.description}
                </p>
              </div>

              {/* Score Input */}
              <div className="flex flex-col items-center gap-2 min-w-[80px]">
                <label className="text-xs font-medium text-muted-foreground">Score</label>
                <div className="flex items-center gap-1">
                  <Input
                    type="number"
                    min="0"
                    max="10"
                    value={log.score}
                    onChange={(e) => updateScore(log.id, parseInt(e.target.value) || 0)}
                    className="w-12 h-8 text-center text-sm font-bold bg-score-input border-border focus:ring-primary"
                  />
                  <span className="text-xs text-muted-foreground">/10</span>
                </div>
                <div className={`text-xs font-medium ${getScoreColor(log.score)}`}>
                  {log.score >= 8 ? "Excellent" : log.score >= 6 ? "Good" : "Needs Work"}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Summary */}
      <Card className="p-4 bg-gradient-primary/10 border-primary/20">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">Session Average</p>
            <p className="text-xs text-muted-foreground">Overall performance score</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-primary">
              {(activityLogs.reduce((sum, log) => sum + log.score, 0) / activityLogs.length).toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground">out of 10</div>
          </div>
        </div>
      </Card>

      {/* Close Button */}
      <div className="flex justify-end pt-4">
        <Button 
          onClick={onClose}
          className="bg-gradient-primary hover:opacity-90 transition-opacity"
        >
          Close Session
        </Button>
      </div>
    </div>
  );
}