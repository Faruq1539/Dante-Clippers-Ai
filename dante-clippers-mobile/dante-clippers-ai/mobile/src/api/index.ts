import { api } from './client';
import type { User, SourceVideo, ProcessingJob, Clip, CreditBalance } from '../types';

export const usersApi = {
  me: () => api.get<User>('/users/me'),
};

export const creditsApi = {
  balance: () => api.get<CreditBalance>('/credits/balance'),
};

export const videosApi = {
  list: () => api.get<SourceVideo[]>('/videos'),

  /**
   * Uploads a video file picked/recorded on the phone. `fileUri` is the
   * local file:// URI React Native gives you from expo-image-picker.
   */
  upload: (fileUri: string, fileName: string, mimeType: string) => {
    const formData = new FormData();
    // React Native's fetch/FormData accepts this object shape for files --
    // it's not a real Blob, but RN's networking layer understands it.
    formData.append('file', {
      uri: fileUri,
      name: fileName,
      type: mimeType,
    } as unknown as Blob);

    return api.post<SourceVideo>('/videos/upload', formData);
  },
};

export const jobsApi = {
  create: (sourceVideoId: string) => api.post<ProcessingJob>('/jobs', { source_video_id: sourceVideoId }),
  get: (jobId: string) => api.get<ProcessingJob>(`/jobs/${jobId}`),
};

export const clipsApi = {
  listForJob: (jobId: string) => api.get<Clip[]>(`/clips/by-job/${jobId}`),
};
