import { describe, expect, it } from 'vitest'
import { sceneCampaign, sceneKey, sceneQuery, sceneSource } from '../src/utils/scene'
describe('business/exhibition attribution', () => {
 it('only accepts positive safe campaign IDs and known sources', () => {
  expect(sceneCampaign('1')).toBe(1)
  for (const value of ['0', '-1', 'bad', '1.2', '9007199254740993']) expect(sceneCampaign(value)).toBeUndefined()
  expect(sceneSource('qr')).toBe('qr')
  expect(sceneSource('javascript:')).toBe('link')
 })
 it('keeps event and business histories in different buckets', () => {
  expect(sceneKey('one', 1, 'qr')).not.toBe(sceneKey('one', undefined, 'qr'))
  expect(sceneKey('one', 1, 'qr')).not.toBe(sceneKey('two', 1, 'qr'))
  expect(sceneQuery('qr', 1)).toEqual({s:'qr',e:'1'})
  expect(sceneQuery('link')).toEqual({s:'link'})
 })
})
