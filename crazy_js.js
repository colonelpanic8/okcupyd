function (value)
{
  var child=parseInt(value);
  var second=(!util.isBitSetInMask(value,this.kids_map.HAS_NONE)&&
              !util.isBitSetInMask(value,this.kids_map.HAS_MANY)&&
              !util.isBitSetInMask(value,this.kids_map.HAS_ONE));
  if(!util.isBitSetInMask(value, this.kids_map.MAYBE_WANTS_UNKNOWN)&&
     !util.isBitSetInMask(value,this.kids_map.YES_WANTS_UNKNOWN)&&
     !util.isBitSetInMask(value,this.kids_map.NO_WANTS_UNKNOWN)){
    if(util.isBitSetInMask(value,this.kids_map.HAS_NONE)){
      child+=util.toMask(this.kids_map.MAYBE_WANTS_HAS_NONE,
                         this.kids_map.YES_WANTS_HAS_NONE,
                         this.kids_map.NO_WANTS_HAS_NONE);
    }

    if(util.isBitSetInMask(value,this.kids_map.HAS_ONE)){
      child+=util.toMask(this.kids_map.MAYBE_WANTS_HAS_ONE
                         this.kids_map.YES_WANTS_HAS_ONE
                         this.kids_map.NO_WANTS_HAS_ONE);
    }

    if(util.isBitSetInMask(value,this.kids_map.HAS_MANY)){
      child+=util.toMask(this.kids_map.MAYBE_WANTS_HAS_MANY
                         this.kids_map.YES_WANTS_HAS_MANY
                         this.kids_map.NO_WANTS_HAS_MANY);
    }
  }
  else{
    if(util.isBitSetInMask(value,this.kids_map.MAYBE_WANTS_UNKNOWN)){
      child-=this.kids_mask.MAYBE_WANTS;
      var list=util.fromMaskToList(child);
      if(second){
        child+=util.toMask(this.kids_map.MAYBE_WANTS_UNKNOWN
                           this.kids_map.MAYBE_WANTS_HAS_ONE
                           this.kids_map.MAYBE_WANTS_HAS_MANY
                           this.kids_map.MAYBE_WANTS_HAS_NONE);
      }

      for(j in list){
        switch(list[j]){
        case this.kids_map.HAS_ONE:child+=util.toMask(this.kids_map.MAYBE_WANTS_HAS_ONE);
          break;
        case this.kids_map.HAS_MANY:child+=util.toMask(this.kids_map.MAYBE_WANTS_HAS_MANY);
          break;
        case this.kids_map.HAS_NONE:child+=util.toMask(this.kids_map.MAYBE_WANTS_HAS_NONE);
          break;
        }
      }
    }

    if(util.isBitSetInMask(value,this.kids_map.YES_WANTS_UNKNOWN)){
      child-=this.kids_mask.YES_WANTS;
      var list=util.fromMaskToList(child);
      if(second){
        child+=util.toMask(this.kids_map.YES_WANTS_UNKNOWN
                           this.kids_map.YES_WANTS_HAS_ONE
                           this.kids_map.YES_WANTS_HAS_MANY
                           this.kids_map.YES_WANTS_HAS_NONE);
      }

      for(j in list){
        switch(list[j]){
        case this.kids_map.HAS_ONE:child+=util.toMask(this.kids_map.YES_WANTS_HAS_ONE);
          break;
        case this.kids_map.HAS_MANY:child+=util.toMask(this.kids_map.YES_WANTS_HAS_MANY);
          break;
        case this.kids_map.HAS_NONE:child+=util.toMask(this.kids_map.YES_WANTS_HAS_NONE);
          break;
        }
      }
    }

    if(util.isBitSetInMask(value,this.kids_map.NO_WANTS_UNKNOWN)){
      child-=this.kids_mask.NO_WANTS;
      var list=util.fromMaskToList(child);
      if(second){
        child+=util.toMask(4,5,this.kids_map.NO_WANTS_UNKNOWN
                           this.kids_map.NO_WANTS_HAS_ONE
                           this.kids_map.NO_WANTS_HAS_MANY
                           this.kids_map.NO_WANTS_HAS_NONE);
      }

      for(j in list){
        switch(list[j]){
        case this.kids_map.HAS_ONE:child+=util.toMask(this.kids_map.NO_WANTS_HAS_ONE);
          break;
        case this.kids_map.HAS_MANY:child+=util.toMask(this.kids_map.NO_WANTS_HAS_MANY);
          break;
        case this.kids_map.HAS_NONE:child+=util.toMask(this.kids_map.NO_WANTS_HAS_NONE);
          break;
        }
      }
    }

    if(!second){
      var jist=util.fromMaskToList(child);
      for(b in jist){
        switch(jist[b]){
        case this.kids_map.HAS_ONE:child-=this.kids_mask.HAS_ONE;
          break;
        case this.kids_map.HAS_MANY:child-=this.kids_mask.HAS_MANY;
          break;
        case this.kids_map.HAS_NONE:child-=this.kids_mask.HAS_NONE;
          break;
        }
      }
    }
  }

  return child;

}
