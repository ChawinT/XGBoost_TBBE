# Multi-threaded BBE integrated with Opinion Dynamics Platform.

This project contains all code for the thesis 'Exploring opinion dynamics of agent-based bettors in an in-play betting exchange’ by Rasa Guzelyte

Executive summary:

This  thesis  describes  the  design  and  integration  of  opinion  dynamics  to  an  open-source,  agent-basedbetting exchange simulation platform called Bristol Betting Exchange (BBE) [2] using a multi-threadedBBE  implementation  introduced  by  Keenet. et al.   A  solution  of  modeling  bettor  opinions  aboutcompetitor chances of winning a race is proposed as a weighted sum of three channels of information aboutthe race.  Specifically, the impact of local (private) and global population sentiment about the competitorsis considered for modelling the impact on bettor opinions. Additionally, the concept of ground truth is alsointroduced to mimic the nature of sports betting events where at the end the winner is announced i.e., the‘true’ opinion is established.  Existing opinion dynamics models like Bounded Confidence (Krause ;Hegselmann  and  Krause ),  Relative  Agreement  (Deffuantet  et al.,  Meadows  and  Cliff )and Relative  Disagreement  (Meadows  and  Cliff)  are  used  for  modeling  the  impact  of  private  bettorconversations on their opinions.  The BBE platform provides the ability to simulate track-racing (e.g.,horse-racing or bicycle racing) events together with customer and competitor interactions during in-playbetting for that event market.  This introduces an experimental environment for understanding bettorbehaviour  and  testing  any  artificial  intelligence  (AI)  and  machine  learning  (ML)  applications  underrepeatable market conditions.  Existing BBE agent-bettors with zero or minimal levels of intelligence areextended to become opinionated with the ability to generate and share their beliefs about a pre-definedcompetitor to create an opinionated population of bettors.  A separate class of bettors is then used tomodel the impact of different information channels about the competitor on their opinions as the track-racing event evolves until the winner is known.  Following this, opinion dynamics of bettors in scenarioswith various bettor populations, peer-to-peer influences and track-racing event simulations are explored.


The original multi-threaded BBE implementation used in this project has been implemented by James Keen and is available here:

https://github.com/keenjam/BettingExchange

