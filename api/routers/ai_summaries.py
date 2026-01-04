"""
AI-generated summaries for predictions using Groq.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
import requests
from typing import Optional

from ..auth import verify_api_key
from ..services.data_loader import load_predictions, load_player_logs

router = APIRouter(prefix="/ai", tags=["AI Summaries"])


class GenerateSummaryRequest(BaseModel):
    """Request to generate AI summary for a prediction"""
    player_id: int
    game_id: str
    prediction_type: str = "shots"  # Future: could support goals, points, etc.


class SummaryResponse(BaseModel):
    """AI-generated summary response"""
    summary: str
    generated_at: str


def get_groq_api_key() -> str:
    """Get Groq API key from environment"""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured. Please set the environment variable."
        )
    return api_key


def build_prompt(prediction_data: dict) -> str:
    """
    Build the prompt for AI summary generation.

    Args:
        prediction_data: Dictionary with player stats and prediction info

    Returns:
        Formatted prompt string
    """
    is_over = 'OVER' in prediction_data['recommendation']

    if is_over:
        prompt = f"""You are a confident sports betting analyst. Write a compelling summary for this HIGH confidence NHL OVER pick.

Pick Details:
- Player: {prediction_data['player_name']} ({prediction_data['team']}) vs {prediction_data['opponent']}
- Recommendation: {prediction_data['recommendation']}
- Model Prediction: {prediction_data['model_prediction']:.1f} shots
- Line: {prediction_data['line']}
- Edge: {prediction_data['edge']:.1f}%
- Best Recent Form: {prediction_data.get('best_avg', 'N/A')} SOG/game ({prediction_data.get('avg_label', 'recent')})
- Season Average: {prediction_data.get('season_avg', 'N/A')} SOG/game

Write a punchy 1-2 sentence summary (under 40 words) that sells this OVER pick. Use POSITIVE language - the player is performing well. Focus on:
- The most compelling stat that supports the pick
- The edge percentage to show value
- Confident, engaging language that varies in structure

Good examples:
- "{prediction_data['player_name']} crushing it with {prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}. Model projects {prediction_data['model_prediction']:.1f} shots for a {prediction_data['edge']:.1f}% edge."
- "Strong {prediction_data['edge']:.1f}% edge on {prediction_data['player_name']}. Firing at {prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}, well above the {prediction_data['line']} line."
- "{prediction_data['player_name']} on fire lately—{prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}. Model loves the over {prediction_data['line']} with {prediction_data['edge']:.1f}% edge."
- "{prediction_data['player_name']} rolling at {prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}. {prediction_data['edge']:.1f}% edge makes this over a high-value play."

Your summary (text only, no quotes):"""
    else:
        prompt = f"""You are a confident sports betting analyst. Write a compelling summary for this HIGH confidence NHL UNDER pick.

Pick Details:
- Player: {prediction_data['player_name']} ({prediction_data['team']}) vs {prediction_data['opponent']}
- Recommendation: {prediction_data['recommendation']}
- Model Prediction: {prediction_data['model_prediction']:.1f} shots
- Line: {prediction_data['line']}
- Edge: {prediction_data['edge']:.1f}%
- Best Recent Form: {prediction_data.get('best_avg', 'N/A')} SOG/game ({prediction_data.get('avg_label', 'recent')})
- Season Average: {prediction_data.get('season_avg', 'N/A')} SOG/game

Write a punchy 1-2 sentence summary (under 40 words) that sells this UNDER pick. Use NEGATIVE language - the player is underperforming or struggling. Focus on:
- The most compelling stat that supports the pick
- The edge percentage to show value
- Confident, engaging language that varies in structure

Good examples:
- "{prediction_data['player_name']}'s recent form suggests downturn with {prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}. Model projects {prediction_data['model_prediction']:.1f} shots for a {prediction_data['edge']:.1f}% edge on under {prediction_data['line']}."
- "{prediction_data['player_name']} struggling at {prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}. Strong {prediction_data['edge']:.1f}% edge on the under {prediction_data['line']}."
- "{prediction_data['player_name']} has cooled off—just {prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}. Model sees {prediction_data['edge']:.1f}% edge under {prediction_data['line']}."
- "Downturn for {prediction_data['player_name']} with {prediction_data.get('best_avg', 'X.X')} SOG {prediction_data.get('avg_label', 'recently')}. {prediction_data['edge']:.1f}% edge makes under {prediction_data['line']} a solid play."

Your summary (text only, no quotes):"""

    return prompt


def call_groq_api(prompt: str, api_key: str) -> str:
    """
    Call Groq API to generate summary.

    Args:
        prompt: The formatted prompt
        api_key: Groq API key

    Returns:
        Generated summary text
    """
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",  # Fast, free Groq model
        "messages": [
            {
                "role": "system",
                "content": "You are a concise sports betting analyst. Keep responses under 40 words."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.8,  # Add variety
        "max_tokens": 100,   # Keep it short
        "top_p": 1,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        result = response.json()
        summary = result['choices'][0]['message']['content'].strip()

        # Remove quotes if AI wrapped the response in quotes
        if summary.startswith('"') and summary.endswith('"'):
            summary = summary[1:-1]

        return summary

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Groq API error: {str(e)}"
        )


@router.post("/generate-summary", response_model=SummaryResponse)
async def generate_ai_summary(
    request: GenerateSummaryRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Generate AI summary for a specific prediction.

    This endpoint:
    1. Loads the prediction data
    2. Loads player recent stats
    3. Builds a prompt with all relevant info
    4. Calls Groq API to generate summary
    5. Returns the generated text

    Args:
        request: GenerateSummaryRequest with player_id and game_id
        api_key: API key from header (required)

    Returns:
        SummaryResponse with generated summary text
    """
    # Load predictions data
    predictions_df = load_predictions()

    # Find the specific prediction
    prediction = predictions_df[
        (predictions_df['player_id'] == request.player_id) &
        (predictions_df['game_id'] == request.game_id)
    ]

    if len(prediction) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Prediction not found for player_id={request.player_id}, game_id={request.game_id}"
        )

    pred_row = prediction.iloc[0]

    # Load player stats for recent performance
    player_logs_df = load_player_logs()
    player_logs = player_logs_df[player_logs_df['player_id'] == request.player_id].copy()

    # Calculate recent averages
    if len(player_logs) > 0:
        player_logs = player_logs.sort_values('game_date', ascending=False)
        last_5_avg = player_logs.head(5)['shots'].mean()
        last_10_avg = player_logs.head(10)['shots'].mean()
        season_avg = player_logs['shots'].mean()

        # Pick the best average based on recommendation
        # For OVER picks: use the highest average (most bullish)
        # For UNDER picks: use the lowest average (most bearish)
        averages = [
            (last_5_avg, 'last 5 games', 'L5'),
            (last_10_avg, 'last 10 games', 'L10'),
            (season_avg, 'this season', 'Season')
        ]

        if 'OVER' in pred_row['recommendation']:
            best_avg, avg_label, time_filter = max(averages, key=lambda x: x[0])
        else:  # UNDER
            best_avg, avg_label, time_filter = min(averages, key=lambda x: x[0])
    else:
        best_avg = None
        avg_label = 'recent games'
        season_avg = None
        time_filter = 'Season'

    # Build prediction data for prompt
    prediction_data = {
        'player_name': pred_row['player_name'],
        'team': pred_row['team'],
        'opponent': pred_row['away_team'] if pred_row['team'] in pred_row['home_team'] else pred_row['home_team'],
        'recommendation': pred_row['recommendation'],
        'model_prediction': pred_row['prediction'],
        'line': pred_row['line'],
        'edge': pred_row.get('true_edge', pred_row.get('edge', 0)) or 0,
        'best_avg': round(best_avg, 1) if best_avg else None,
        'avg_label': avg_label,
        'season_avg': round(season_avg, 1) if season_avg else None,
    }

    # Build prompt
    prompt = build_prompt(prediction_data)

    # Get Groq API key
    groq_api_key = get_groq_api_key()

    # Generate summary
    summary = call_groq_api(prompt, groq_api_key)

    # Return response
    from datetime import datetime
    return SummaryResponse(
        summary=summary,
        generated_at=datetime.now().isoformat()
    )