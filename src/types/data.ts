/**
 * Canonical data types — mirror scripts/pipeline/schema.py exactly.
 *
 * If you change one, change the other. The pipeline emits JSON that the
 * frontend loads at build time (or at runtime via fetch from the data branch).
 */

export interface BilingualText {
  en: string;
  ar: string;
}

export interface Narrative {
  text: BilingualText;
  generated_at: string;
  /** "template" | "qwen2.5-1.5b" */
  source: string;
}

export interface PlayerSeasonStats {
  matches: number;
  starts: number;
  minutes: number;
  goals: number;
  assists: number;
  yellow_cards: number;
  red_cards: number;
  xg: number | null;
  xa: number | null;
  npxg?: number | null;
  progressive_carries?: number | null;
  progressive_passes?: number | null;
  shots?: number | null;
  shots_on_target?: number | null;
  pass_completion_pct?: number | null;
  tackles?: number | null;
  interceptions?: number | null;
  aerials_won_pct?: number | null;
  save_pct?: number | null;
  clean_sheets?: number | null;
}

export type Position = 'GK' | 'DF' | 'MF' | 'FW';

export interface Team {
  id: string;
  name: BilingualText;
  short_name: BilingualText;
  fbref_id: string | null;
  wikidata_id: string | null;
  founded: number | null;
  city: BilingualText | null;
  crest_url: string | null;
  primary_color: string | null;
  sources: Record<string, string>;
}

export interface Player {
  id: string;
  name: BilingualText;
  team_id: string | null;
  position: Position | null;
  detailed_position: string | null;
  jersey_number: number | null;
  nationality: BilingualText | null;
  birth_date: string | null;
  height_cm: number | null;
  foot: string | null;
  photo_url: string | null;
  fbref_id: string | null;
  wikidata_id: string | null;
  season_stats: PlayerSeasonStats;
  scout_report?: Narrative | null;
  sources: Record<string, string>;
}

export type FixtureStatus = 'scheduled' | 'live' | 'finished' | 'postponed';

export type MatchEventType =
  | 'goal'
  | 'own_goal'
  | 'penalty'
  | 'yellow'
  | 'red'
  | 'sub';

export interface MatchEvent {
  minute: number;
  team_id: string;
  type: MatchEventType;
  player_id: string | null;
  player_name: BilingualText | null;
  detail: BilingualText | null;
}

export interface XgFlowPoint {
  minute: number;
  home_xg: number;
  away_xg: number;
}

export interface Fixture {
  id: string;
  date: string;
  kickoff: string | null;
  matchweek: number | null;
  home_team_id: string;
  away_team_id: string;
  venue: BilingualText | null;
  home_goals: number | null;
  away_goals: number | null;
  home_xg: number | null;
  away_xg: number | null;
  status: FixtureStatus;
  fbref_match_id: string | null;
  events: MatchEvent[];
  xg_flow: XgFlowPoint[];
  preview?: Narrative | null;
  recap?: Narrative | null;
  sources: Record<string, string>;
}

export interface FeatureContribution {
  feature: string;
  label: BilingualText;
  /** signed pp impact on home-win probability */
  value: number;
  explanation: BilingualText;
}

export interface MatchPrediction {
  fixture_id: string;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  home_xg_predicted: number;
  away_xg_predicted: number;
  btts_prob: number;
  over25_prob: number;
  /** [home_goals, away_goals] */
  most_likely_score: [number, number];
  contributions: FeatureContribution[];
  generated_at: string;
  model_version: string;
}

export interface SeasonSnapshot {
  league_id: string;
  season: string;
  generated_at: string;
  teams: Team[];
  players: Player[];
  fixtures: Fixture[];
  predictions?: MatchPrediction[];
}

export interface DataManifest {
  generated_at: string;
  version: string;
  stage: string;
  league: string;
  season: string;
  team_count?: number;
  player_count?: number;
}
