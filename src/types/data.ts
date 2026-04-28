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
  sources: Record<string, string>;
}

export type FixtureStatus = 'scheduled' | 'live' | 'finished' | 'postponed';

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
  status: FixtureStatus;
  fbref_match_id: string | null;
  sources: Record<string, string>;
}

export interface SeasonSnapshot {
  league_id: string;
  season: string;
  generated_at: string;
  teams: Team[];
  players: Player[];
  fixtures: Fixture[];
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
