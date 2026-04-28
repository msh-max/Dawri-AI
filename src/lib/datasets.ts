/**
 * Helpers that wrap the data loader for build-time use in pages.
 *
 * Centralizes the "by id" lookups so pages stay terse.
 */

import type { Player, SeasonSnapshot, Team } from '@/types/data';
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
