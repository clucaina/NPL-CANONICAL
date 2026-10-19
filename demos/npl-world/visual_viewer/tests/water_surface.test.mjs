import test from 'node:test';
import assert from 'node:assert/strict';
import {WATER_SOURCE} from '../water_surface.mjs';
test('water source explicitly illustrative',()=>assert.ok(WATER_SOURCE.includes('not_surveyed')));
