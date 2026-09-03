import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { jobsApi } from '../api';
import type { ProcessingJob } from '../types';
import type { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'JobStatus'>;

const STAGE_LABELS: Record<ProcessingJob['status'], string> = {
  queued: 'Waiting in queue…',
  transcribing: 'Listening to your video…',
  scoring: 'Finding the best moments…',
  rendering: 'Cutting your clips…',
  done: 'Done!',
  failed: 'Something went wrong.',
};

// Real transcription + AI scoring + rendering genuinely takes a while
// (30s-several minutes depending on video length and hardware) -- see
// backend/README.md. Poll every 3s rather than hammering the API.
const POLL_INTERVAL_MS = 3000;

export default function JobStatusScreen({ route, navigation }: Props) {
  const { jobId } = route.params;
  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function poll() {
      try {
        const result = await jobsApi.get(jobId);
        setJob(result);

        if (result.status === 'done') {
          if (intervalRef.current) clearInterval(intervalRef.current);
          navigation.replace('Clips', { jobId: result.id });
        } else if (result.status === 'failed') {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to check job status');
      }
    }

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId, navigation]);

  return (
    <View style={styles.container}>
      {job?.status === 'failed' ? (
        <>
          <Text style={styles.failedTitle}>Processing failed</Text>
          <Text style={styles.failedMessage}>{job.error_message || 'Unknown error'}</Text>
        </>
      ) : (
        <>
          <ActivityIndicator color="#FFFFFF" size="large" />
          <Text style={styles.stageText}>
            {job ? STAGE_LABELS[job.status] : 'Connecting…'}
          </Text>
        </>
      )}
      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0B0F', alignItems: 'center', justifyContent: 'center', padding: 24 },
  stageText: { color: '#FFFFFF', fontSize: 17, marginTop: 20 },
  failedTitle: { color: '#FF6B6B', fontSize: 20, fontWeight: '700' },
  failedMessage: { color: '#9A9AA5', fontSize: 14, marginTop: 12, textAlign: 'center' },
  errorText: { color: '#FF6B6B', marginTop: 16, fontSize: 13 },
});
