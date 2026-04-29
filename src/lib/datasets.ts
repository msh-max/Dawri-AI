/**
 * Helpers that wrap the data loader for build-time use in pages.
 *
 * Centralizes the "by id" lookups so pages stay terse.
 */

import type {
  Fixture,
  MatchPrediction,
  Player,
  SeasonSnapshot,
  Team,
} from '@/types/data';
import { loadSeasonSnapshot } from './data';

let _cached: Promise<SeasonSnapshot> | null = null;

export function getSeason(): Promise<SeasonSnapshot> {
  if (!_cached) _cached = loadSeasonSnapshot();
  return _cached;
}

export async function getAllPlayers(): Promise<Player[]> {
  return (await getSeason()).players;
}

export async function getAllTeams(): Promise<Team[]> {
  return (await getSeason()).teams;
}

export async function getPlayerById(id: string): Promise<Player | null> {
  return (await getAllPlayers()).find((p) => p.id === id) ?? null;
}

export async function getTeamById(id: string): Promise<Team | null> {
  return (await getAllTeams()).find((t) => t.id === id) ?? null;
}

export async function getPlayersForTeam(teamId: string): Promise<Player[]> {
  return (await getAllPlayers()).filter((p) => p.team_id === teamId);
}

export async function getAllFixtures(): Promise<Fixture[]> {
  return (await getSeason()).fixtures;
}

export async function getFixtureById(id: string): Promise<Fixture | null> {
  return (await getAllFixtures()).find((f) => f.id === id) ?? null;
}

export async function getFixturesForTeam(teamId: string): Promise<Fixture[]> {
  return (await getAllFixtures()).filter(
    (f) => f.home_team_id === teamId || f.away_team_id === teamId
  );
}

export async function getPredictionForFixture(
  fixtureId: string
): Promise<MatchPrediction | null> {
  const season = await getSeason();
  return season.predictions?.find((p) => p.fixture_id === fixtureId) ?? null;
}

export async function getAllPredictions(): Promise<MatchPrediction[]> {
  return (await getSeason()).predictions ?? [];
}
