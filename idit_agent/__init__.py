"""
idit-agent-kit — Drop-in library for AI agents to sign entries to a Personal Idit chain.

Usage:
    from idit_agent import IditAgent

    agent = IditAgent(signer="my-agent", model="gpt-4o")
    entry = agent.mint("Completed the quarterly report analysis.")

That's it. Your agent is now signing to a verifiable chain.
"""

from .agent import IditAgent

__version__ = "0.1.0"
__all__ = ["IditAgent"]
