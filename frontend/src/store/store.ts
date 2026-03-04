import { configureStore } from '@reduxjs/toolkit';
import weatherReducer from './weatherSlice';
import cyberReducer from './cyberSlice';
import blackoutReducer from './blackoutSlice';
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';

export const store = configureStore({
  reducer: {
    weather: weatherReducer,
    cyber: cyberReducer,
    blackout: blackoutReducer
  }
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
