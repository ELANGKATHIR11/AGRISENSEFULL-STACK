/**
 * AI Models Service - Phi LLM & SCOLD VLM Integration
 * 
 * This service provides frontend integration with:
 * - Phi LLM: Lightweight language model for chatbot enhancement
 * - SCOLD VLM: Vision Language Model for disease/weed detection
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8004';

// ============================================================
// Type Definitions
// ============================================================

export interface PhiStatus {
  available: boolean;
  endpoint: string;
  model: string;
  status: 'available' | 'unavailable';
}

export interface ScoldStatus {
  available: boolean;
  base_url: string;
  model: string;
  features: string[];
  status: 'available' | 'unavailable';
}

export interface ModelsStatus {
  phi: PhiStatus;
  scold: ScoldStatus;
  timestamp: string;
}

export interface EnrichResponse {
  success: boolean;
  enriched_answer: string;
  original_answer: string;
  metadata?: {
    model: string;
    processing_time: number;
  };
  error?: string;
}

export interface RerankRequest {
  question: string;
  answers: string[];
}

export interface RerankResponse {
  success: boolean;
  ranked_answers: Array<{
    answer: string;
    score: number;
    rank: number;
  }>;
  metadata?: {
    model: string;
    processing_time: number;
  };
  error?: string;
}

export interface ContextualRequest {
  question: string;
  conversation_history?: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
  context?: Record<string, any>;
}

export interface ContextualResponse {
  success: boolean;
  response: string;
  metadata?: {
    model: string;
    processing_time: number;
  };
  error?: string;
}

export interface DiseaseDetection {
  disease: string;
  confidence: number;
  bbox?: [number, number, number, number];
  severity?: string;
  affected_area_percent?: number;
  treatment?: {
    immediate_actions: string[];
    organic_methods: string[];
    chemical_options: string[];
    preventive_measures: string[];
  };
}

export interface ScoldDiseaseResponse {
  success: boolean;
  detections: DiseaseDetection[];
  crop_type: string;
  timestamp: string;
  metadata?: {
    model: string;
    processing_time: number;
  };
  error?: string;
}

export interface WeedDetection {
  weed_type: string;
  confidence: number;
  bbox?: [number, number, number, number];
  coverage_percent?: number;
  treatment?: {
    manual_removal: string[];
    mulching: string[];
    organic_herbicides: string[];
    chemical_options: string[];
    prevention_tips: string[];
  };
}

export interface ScoldWeedResponse {
  success: boolean;
  detections: WeedDetection[];
  crop_type: string;
  total_weed_coverage: number;
  timestamp: string;
  metadata?: {
    model: string;
    processing_time: number;
  };
  error?: string;
}

// ============================================================
// Phi LLM Functions
// ============================================================

/**
 * Get Phi LLM status
 */
export async function getPhiStatus(): Promise<PhiStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/phi/status`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to get Phi status:', error);
    return {
      available: false,
      endpoint: 'http://localhost:11434',
      model: 'phi',
      status: 'unavailable'
    };
  }
}

/**
 * Enrich chatbot answer with Phi LLM
 */
export async function enrichChatbotAnswer(
  question: string,
  baseAnswer: string,
  context?: Record<string, any>
): Promise<EnrichResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chatbot/enrich`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        base_answer: baseAnswer,
        context: context || {}
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to enrich answer:', error);
    return {
      success: false,
      enriched_answer: baseAnswer,
      original_answer: baseAnswer,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Rerank chatbot answers with Phi LLM
 */
export async function rerankAnswers(
  question: string,
  answers: string[]
): Promise<RerankResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chatbot/rerank`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        answers
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to rerank answers:', error);
    return {
      success: false,
      ranked_answers: answers.map((answer, idx) => ({
        answer,
        score: 1.0 - idx * 0.1,
        rank: idx + 1
      })),
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Generate contextual response with Phi LLM
 */
export async function generateContextualResponse(
  request: ContextualRequest
): Promise<ContextualResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chatbot/contextual`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to generate contextual response:', error);
    return {
      success: false,
      response: 'Unable to generate response at this time.',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// ============================================================
// SCOLD VLM Functions
// ============================================================

/**
 * Get SCOLD VLM status
 */
export async function getScoldStatus(): Promise<ScoldStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/scold/status`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to get SCOLD status:', error);
    return {
      available: false,
      base_url: 'http://localhost:8001',
      model: 'SCOLD VLM',
      features: [],
      status: 'unavailable'
    };
  }
}

/**
 * Detect diseases using SCOLD VLM
 */
export async function detectDiseaseWithScold(
  imageData: string,
  cropType: string = 'unknown'
): Promise<ScoldDiseaseResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/disease/detect-scold`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_base64: imageData,
        crop_type: cropType
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to detect disease:', error);
    return {
      success: false,
      detections: [],
      crop_type: cropType,
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Detect weeds using SCOLD VLM
 */
export async function detectWeedsWithScold(
  imageData: string,
  cropType: string = 'unknown'
): Promise<ScoldWeedResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/weed/detect-scold`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_base64: imageData,
        crop_type: cropType
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to detect weeds:', error);
    return {
      success: false,
      detections: [],
      crop_type: cropType,
      total_weed_coverage: 0,
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Get overall AI models status
 */
export async function getModelsStatus(): Promise<ModelsStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/models/status`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to get models status:', error);
    const [phi, scold] = await Promise.all([
      getPhiStatus(),
      getScoldStatus()
    ]);
    return {
      phi,
      scold,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * Check if Phi LLM is available
 */
export async function isPhiAvailable(): Promise<boolean> {
  const status = await getPhiStatus();
  return status.available;
}

/**
 * Check if SCOLD VLM is available
 */
export async function isScoldAvailable(): Promise<boolean> {
  const status = await getScoldStatus();
  return status.available;
}
