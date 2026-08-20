import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { useGeolocation } from './use-geolocation';

type PositionError = { code: number; PERMISSION_DENIED: number };

const original = Object.getOwnPropertyDescriptor(Navigator.prototype, 'geolocation');

function setGeolocation(value: unknown): void {
  Object.defineProperty(navigator, 'geolocation', { configurable: true, value });
}

beforeEach(() => setGeolocation(undefined));

afterEach(() => {
  if (original) Object.defineProperty(Navigator.prototype, 'geolocation', original);
  else Reflect.deleteProperty(navigator, 'geolocation');
});

describe('useGeolocation', () => {
  it('reports unsupported browsers without requesting location', () => {
    const { result } = renderHook(() => useGeolocation());
    act(() => result.current.locate());
    expect(result.current.state).toEqual({ status: 'error' });
  });

  it.each([
    [2, 'unavailable'],
    [3, 'timeout'],
  ])('maps %s geolocation failures to the error state', (code) => {
    const getCurrentPosition = (_success: PositionCallback, error: PositionErrorCallback) =>
      error({ code, PERMISSION_DENIED: 1 } as GeolocationPositionError);
    setGeolocation({ getCurrentPosition });
    const { result } = renderHook(() => useGeolocation());
    act(() => result.current.locate());
    expect(result.current.state).toEqual({ status: 'error' });
  });

  it('maps permission denial to denied and never starts watchPosition tracking', () => {
    const watchPosition = () => { throw new Error('watchPosition must not be called'); };
    const getCurrentPosition = (_success: PositionCallback, error: PositionErrorCallback) =>
      error({ code: 1, PERMISSION_DENIED: 1 } as GeolocationPositionError);
    setGeolocation({ getCurrentPosition, watchPosition });
    const { result } = renderHook(() => useGeolocation());
    act(() => result.current.locate());
    expect(result.current.state).toEqual({ status: 'denied' });
    expect(result.current.state.status).not.toBe('requesting');
  });
});