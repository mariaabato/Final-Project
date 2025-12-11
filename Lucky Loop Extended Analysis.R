# Lucky Loop+ Extended Analysis 
# Reads results.csv and produces summary statistics, plots, and advanced insights
# Author: Maria Abato

# Before you read: This data and the resulting graphs are most likely not indicative of the actual statistics of my game.
# I just thought the concept of a game that collects the stats of players would be interesting
# In a perfect world where this game had multiple players other than myself, players would be able to access their own data and compare it to the average data of all players


# Setup
setwd("/Users/mariaabato/Desktop/CIS1051 Undemoed Labs/Everything Final Project")

# Load libraries
library(ggplot2)
library(dplyr)
library(scales)
library(zoo)
library(reshape2)

# Read data
results <- read.csv("results.csv", stringsAsFactors = FALSE)

# Ensure correct data types
results$Round <- as.numeric(results$Round)
results$Level <- as.numeric(results$Level)
results$PlayerValue <- as.numeric(results$PlayerValue)
results$DealerValue <- as.numeric(results$DealerValue)
results$Reward <- as.numeric(results$Reward)
results$Balance <- as.numeric(results$Balance)
results$Result <- tolower(results$Result)

# Define Bet Era
results <- results %>%
  mutate(BetEra = ifelse(Round <= 51, "Low Bet", "High Bet"))

# Basic Summary Stats
total_rounds <- nrow(results)
win_rate <- mean(results$Result == "win")
avg_balance <- mean(results$Balance, na.rm = TRUE)
avg_reward <- mean(results$Reward, na.rm = TRUE)

cat("Total rounds:", total_rounds, "\n")
cat("Win rate:", round(win_rate*100,2), "%\n")
cat("Average balance:", round(avg_balance,2), "\n")
cat("Average reward per round:", round(avg_reward,2), "\n\n")

# Win rate and average reward by Bet Era
win_by_era <- results %>%
  group_by(BetEra) %>%
  summarise(WinRate = mean(Result=="win"),
            AvgReward = mean(Reward, na.rm=TRUE),
            AvgBalance = mean(Balance, na.rm=TRUE))
print(win_by_era)

cat("\nSummary Table Analysis:\n")
#This table shows that when I was using lower bets, wins and rewards were smaller, while when making higher bets, rewards and balance changes are much larger. It reflects the impact of increasing bets on overall game performance
# Win rate by Level, Skill, Encounter
win_by_level <- results %>%
  group_by(Level) %>%
  summarise(WinRate = mean(Result=="win"))

win_by_skill <- results %>%
  group_by(Skill) %>%
  summarise(WinRate = mean(Result=="win"))

win_by_encounter <- results %>%
  group_by(Encounter) %>%
  summarise(WinRate = mean(Result=="win"))

reward_by_level <- results %>%
  group_by(Level) %>%
  summarise(AvgReward = mean(Reward, na.rm=TRUE))

reward_by_encounter <- results %>%
  group_by(Encounter) %>%
  summarise(AvgReward = mean(Reward, na.rm=TRUE))

# Cumulative Metrics
results <- results %>%
  arrange(Round) %>%
  mutate(CumReward = cumsum(Reward),
         CumWins = cumsum(Result=="win"))

# Rolling Balance and Balance Change by BetEra
results <- results %>%
  group_by(BetEra) %>%
  arrange(Round) %>%
  mutate(RollingBalanceEra = zoo::rollmean(Balance, k=5, fill=NA),
         BalanceChange = c(NA, diff(Balance))) %>%
  ungroup()

# Loss Streak Analysis
results <- results %>%
  mutate(Loss = ifelse(Result=="loss", 1, 0),
         StreakID = cumsum(c(1, diff(Loss)!=0)))

loss_streaks <- results %>%
  filter(Loss==1) %>%
  group_by(StreakID) %>%
  summarise(StreakLength = n()) %>%
  summarise(AvgLossStreak = mean(StreakLength))

cat("Average loss streak length:", loss_streaks$AvgLossStreak, "\n\n")
#Longer loss streaks may indicate risky rounds or unlucky sequences. Players may want to adjust strategy if loss streaks are frequent

# -------------------------
# Plots with Interpretations
# -------------------------

# 1. Balance over time by Bet Era
p1 <- ggplot(results, aes(x=Round, y=Balance, color=BetEra)) +
  geom_line(size=1) +
  ggtitle("Balance Over Time by Bet Era") +
  xlab("Round") + ylab("Balance ($)")
ggsave("balance_by_betera.png", width=8, height=4)
p1
#The plot shows slow growth in early low-bet rounds and larger swings in high-bet rounds, highlighting the effect of bet size on total balance
# 2. Rolling average balance by Bet Era
p2 <- ggplot(results, aes(x=Round, y=RollingBalanceEra, color=BetEra)) +
  geom_line(size=1) +
  ggtitle("Rolling Average Balance (5 rounds) by Bet Era") +
  xlab("Round") + ylab("Balance ($)")
ggsave("rolling_balance_betera.png", width=8, height=4)
p2
#Rolling averages smooth fluctuations and show general trends. High-bet era contributes more to overall balance growth

# 3. Balance change per round by Bet Era
p3 <- ggplot(results, aes(x=Round, y=BalanceChange, fill=BetEra)) +
  geom_col(position="dodge") +
  ggtitle("Balance Change per Round by Bet Era") +
  xlab("Round") + ylab("Balance Change ($)") +
  theme_minimal()
ggsave("balance_change_betera.png", width=8, height=4)
p3
#Each round's gain/loss is more dramatic in high-bet rounds. Low-bet rounds have smaller, steadier changes
# 4. Win rate by Level
p4 <- ggplot(win_by_level, aes(x=factor(Level), y=WinRate)) +
  geom_col(fill="skyblue") +
  scale_y_continuous(labels = percent) +
  ggtitle("Win Rate by Level") + xlab("Level") + ylab("Win Rate")
ggsave("winrate_by_level.png", width=6, height=4)
p4
#Shows which game levels are easier or harder to win. Higher levels may correspond to higher difficulty or tougher encounters

# 5. Win rate by Skill
p5 <- ggplot(win_by_skill, aes(x=reorder(Skill, WinRate), y=WinRate)) +
  geom_col(fill="orange") +
  coord_flip() +
  scale_y_continuous(labels = percent) +
  ggtitle("Win Rate by Skill") + xlab("Skill") + ylab("Win Rate")
ggsave("winrate_by_skill.png", width=6, height=4)
p5
#Certain skills consistently yield higher win rates, indicating which strategies or player choices are most effective

# 6. Win rate by Encounter
p6 <- ggplot(win_by_encounter, aes(x=reorder(Encounter, WinRate), y=WinRate)) +
  geom_col(fill="purple") +
  coord_flip() +
  scale_y_continuous(labels = percent) +
  ggtitle("Win Rate by Encounter") + xlab("Encounter") + ylab("Win Rate")
ggsave("winrate_by_encounter.png", width=6, height=4)
p6
#Some encounters are easier to win, while others consistently reduce win rate, highlighting riskier game events

# 7. Reward distribution
p7 <- ggplot(results, aes(x=Reward)) +
  geom_histogram(bins=15, fill="cyan", color="black") +
  ggtitle("Reward Distribution") + xlab("Reward") + ylab("Count") +
  theme_minimal()
ggsave("reward_distribution.png", width=6, height=4)
p7
#Most rounds yield small rewards (especially low-bet rounds). High-bet rounds generate larger spikes in reward

# 8. Balance over time by Level
p8 <- ggplot(results, aes(x=Round, y=Balance, color=factor(Level))) +
  geom_line() +
  ggtitle("Balance Over Time by Level") + xlab("Round") + ylab("Balance ($)") +
  labs(color="Level")
ggsave("balance_by_level.png", width=8, height=4)
p8
#Shows how different levels affect balance growth. Some levels produce faster gains than others

# 9. Cumulative reward over rounds
p9 <- ggplot(results, aes(x=Round, y=CumReward)) +
  geom_line(color="darkgreen") +
  ggtitle("Cumulative Reward Over Rounds") + xlab("Round") + ylab("Cumulative Reward ($)")
ggsave("cumulative_reward.png", width=8, height=4)
p9
#Overall gains are slow early on and accelerate in high-bet rounds. Cumulative reward emphasizes total profit across the game

# 10. Outcome counts by Skill
p10 <- results %>% group_by(Skill, Result) %>% summarise(Count = n()) %>%
  ggplot(aes(x=Skill, y=Count, fill=Result)) +
  geom_col(position="dodge") +
  ggtitle("Outcome Counts by Skill") + xlab("Skill") + ylab("Count")
ggsave("outcomes_by_skill.png", width=8, height=4)
p10
#Highlights which skills result in more wins, losses, or pushes
# 11. Average reward by Encounter
p11 <- ggplot(reward_by_encounter, aes(x=reorder(Encounter, AvgReward), y=AvgReward)) +
  geom_col(fill="forestgreen") +
  coord_flip() +
  ggtitle("Average Reward by Encounter") + xlab("Encounter") + ylab("Average Reward ($)")
ggsave("avg_reward_by_encounter.png", width=6, height=4)
p11
#Some encounters yield higher rewards on average. High-risk encounters may offer bigger wins

# 12. Win rate by Player Value
win_by_playervalue <- results %>%
  group_by(PlayerValue) %>%
  summarise(WinRate = mean(Result=="win"))

p12 <- ggplot(win_by_playervalue, aes(x=PlayerValue, y=WinRate)) +
  geom_line(color="blue") +
  scale_y_continuous(labels = percent) +
  ggtitle("Win Rate by Player Hand Value") + xlab("Player Value") + ylab("Win Rate")
ggsave("winrate_by_playervalue.png", width=8, height=4)
p12
#Player hand totals around 18-21 generally have higher win rates, as expected in blackjack strategy

# 13. Heatmap: Player vs Dealer Value Win Rate
heatmap_data <- results %>%
  group_by(PlayerValue, DealerValue) %>%
  summarise(WinRate = mean(Result=="win"))

p13 <- ggplot(heatmap_data, aes(x=PlayerValue, y=DealerValue, fill=WinRate)) +
  geom_tile() +
  scale_fill_gradient(low="red", high="green", labels=scales::percent) +
  ggtitle("Win Rate Heatmap: Player vs Dealer") + xlab("Player Value") + ylab("Dealer Value")
ggsave("heatmap_player_vs_dealer.png", width=8, height=6)
p13
# The heatmap shows how combinations of player and dealer hands affect winning chances. Green areas indicate favorable player totals
