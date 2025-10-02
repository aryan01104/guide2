import { saveSession } from "../database/session_operations.js";

class SessionState {
  // Hard thresholds (minutes)
  static HARD_BREAK_MIN = 10;
  static HARD_WORK_MIN = 15;

  // EMA smoothing factor for per-minute scores
  static EMA_ALPHA = 0.3;

  // Size of rolling raw score buffer (e.g., last 4h at 1-min interval)
  static BUFFER_SIZE = 240;

  constructor() {
    this.current_session = null;
    this.current_context = null;
    this.context_start_time = null;
    this.ema_score = null;
    this.break_counter = 0;
    this.work_counter = 0;
    this.score_buffer = [];
    this.prev_session_meta = null;
    this.prev_activities = [];
  }

  _update_ema(score) {
    if (this.ema_score === null) {
      this.ema_score = score;
    } else {
      this.ema_score =
        this.constructor.EMA_ALPHA * score +
        (1 - this.constructor.EMA_ALPHA) * this.ema_score;
    }
  }

  _update_buffer(score) {
    this.score_buffer.push(score);
    if (this.score_buffer.length > this.constructor.BUFFER_SIZE) {
      this.score_buffer.shift();
    }
  }

  _compute_dynamic_thresholds() {
    const buf = [...this.score_buffer];
    if (buf.length < 10) {
      return [20.0, 0.0];
    }

    const sorted_buf = buf.sort((a, b) => a - b);
    const i75 = Math.floor(0.75 * (sorted_buf.length - 1));
    const i25 = Math.floor(0.25 * (sorted_buf.length - 1));
    return [sorted_buf[i75], sorted_buf[i25]];
  }

  process_minute(activity, score) {
    const now = activity.timestamp_start;
    const raw_score = parseFloat(score || 0);

    this._update_ema(raw_score);
    this._update_buffer(raw_score);

    const [work_thresh, break_thresh] = this._compute_dynamic_thresholds();

    if (this.ema_score < break_thresh) {
      this.break_counter++;
      this.work_counter = 0;
    } else if (this.ema_score > work_thresh) {
      this.work_counter++;
      this.break_counter = 0;
    } else {
      this.break_counter = Math.max(this.break_counter - 1, 0);
      this.work_counter = Math.max(this.work_counter - 1, 0);
    }

    if (
      this.current_session &&
      this.break_counter >= this.constructor.HARD_BREAK_MIN
    ) {
      this._end_session(now);
    } else if (
      !this.current_session &&
      this.work_counter >= this.constructor.HARD_WORK_MIN
    ) {
      this._start_session(activity, now);
    }
  }

  _start_session(activity, start_time) {
    if (this.current_session) {
      this.prev_session_meta = {
        dominant_type: this.current_context,
        start_time: this.current_session.start_time,
        duration: this.current_session.activities.reduce(
          (sum, a) => sum + a.duration_sec,
          0
        ),
        session_type: this.current_context,
      };
      this.prev_activities = [...this.current_session.activities];
    } else {
      this.prev_session_meta = null;
      this.prev_activities = [];
    }

    this.current_session = { activities: [activity], start_time: start_time };
    this.current_context = "productive";
    this.context_start_time = start_time;
    console.log(`[SessionState] ▶️ Session started at ${start_time}`);
  }

  async _end_session(end_time) {
    const acts = this.current_session.activities;
    const session_id = await saveSession(acts);

    console.log(`[SessionState] ⏹️ Session ${session_id} ended at ${end_time}`);

    this.current_session = null;
    this.current_context = null;
    this.context_start_time = null;
    this.break_counter = 0;
    this.work_counter = 0;
    this.ema_score = null;
    this.score_buffer = [];
  }

  add_activity(activity) {
    if (this.current_session) {
      this.current_session.activities.push(activity);
    }
    this.process_minute(activity, activity.productivity_score);
  }
}

export { SessionState };
